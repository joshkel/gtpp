#!/usr/bin/env python3

from colorama import Fore, Style
from functools import wraps
import re
import sys


def handle(regex):
    if isinstance(regex, str):
        regex = re.compile(regex)

    def decorator(f):
        @wraps(f)
        def wrapper(self, line):
            m = regex.search(line)
            if not m:
                return False
            result = f(self, *m.groups())
            if result is not None:
                return result
            else:
                return True

        wrapper.is_handler = True

        return wrapper

    return decorator


def progress(current, total):
    total = str(total)
    return '%*i / ' % (len(total), current) + total


class Parser(object):
    TIME_RE = r'(?: \((\d+) ms(?: total)?\))?'

    def __init__(self):
        members = [getattr(self, i) for i in dir(self)]
        self.handlers = [f for f in members if callable(f) and hasattr(f, 'is_handler')]

        self.total_test_count = 0
        self.total_test_case_count = 0
        self.test_case_index = 0

        self.current_test_case = None
        self.current_test_count = 0
        self.test_index = 0
        self.current_fail_count = 0

        self.in_raw_output = True

    def process(self, line):
        for h in self.handlers:
            if h(line):
                self.in_raw_output = False
                return True

        if not self.in_raw_output:
            self.in_raw_output = True
            print()

    @handle(r'Running (\d+) tests? from (\d+) test cases?')
    def start(self, total_test_count, total_test_case_count):
        self.total_test_count = int(total_test_count)
        self.total_test_case_count = int(total_test_case_count)

    @handle(r'\[-+\] (\d+) tests? from (.*?)' + TIME_RE + '$')
    def start_stop_test_case(self, test_count, test_case, time=None):
        if not self.current_test_case:
            self.current_test_case = test_case
            self.current_test_count = int(test_count)
            self.current_fail_count = 0
            self.test_index = 0
            self.test_case_index += 1
            print(progress(self.test_case_index, self.total_test_case_count) + '   ' + test_case, end='')
        else:
            if not self.current_fail_count:
                print('\r' + progress(self.test_case_index, self.total_test_case_count) + Fore.GREEN + ' ✓ ' + test_case + Style.RESET_ALL, end='')
            else:
                print('\r' + progress(self.test_case_index, self.total_test_case_count) + Fore.RED + ' ✗ ' + test_case + ' - %i/%i failures' % (self.current_fail_count, self.current_test_count) + Style.RESET_ALL, end='')
            if time:
                print(' (%s ms)' % time)
            else:
                print()
            self.current_test_case = None

    @handle(r'\[ *RUN *\] (.*)\.(.*)')
    def start_test(self, test_case, test_count):
        pass

    @handle(r'\[ *(OK|FAILED) *\] (.*)\.(.*?)' + TIME_RE + '$')
    def stop_test(self, status, test_case, test_count, time=None):
        if status == 'FAILED':
            self.current_fail_count += 1

    @handle(r'^$')
    def blank_line(self):
        if self.current_test_case:
            return False


def main():
    parser = Parser()

    for line in sys.stdin:
        if not parser.process(line):
            print(line, end='')


if __name__ == '__main__':
    main()
