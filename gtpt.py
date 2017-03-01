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

    def process(self, line):
        for h in self.handlers:
            if h(line):
                return True

    @handle(r'Running (\d+) tests? from (\d+) test cases?')
    def start(self, total_test_count, total_test_case_count):
        self.total_test_count = total_test_count
        self.total_test_case_count = total_test_case_count

    @handle(r'\[-+\] (\d+) tests? from (.*)' + TIME_RE)
    def start_stop_test_case(self, test_count, test_case, time=None):
        if not self.current_test_case:
            self.current_test_case = test_case
            self.current_test_count = test_count
            self.test_index = 0
            self.test_case_index += 1
            print(progress(self.test_case_index, self.total_test_case_count) + '   ' + test_case, end='')
        else:
            self.current_test_case = None

    @handle(r'\[ *RUN *\] (.*)\.(.*)')
    def start_test(self, test_case, test_count):
        pass

    @handle(r'\[ *(OK|FAILED) *\] (.*)\.(.*)' + TIME_RE)
    def stop_test(self, status, test_case, test_count, time=None):
        pass

    @handle(r'^$')
    def blank_line(self):
        if not self.current_test_case:
            return False


def main():
    parser = Parser()

    for line in sys.stdin:
        if not parser.process(line):
            print(line, end='')


if __name__ == '__main__':
    main()
