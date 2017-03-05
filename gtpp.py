#!/usr/bin/env python3

import argparse
from collections import OrderedDict
from colorama import Fore, Style
from functools import wraps
import re
import sys


class UnicodeCharacters:
    empty = ' '
    success = '✓'
    fail = '✗'


class AsciiCharacters:
    empty = '  '
    success = 'OK'
    fail = ' X'


class LineHandler(object):
    def __init__(self):
        self._handlers = []

    def process(self, owner, line):
        for h in self._handlers:
            if h(owner, line):
                return True

    def add(self, regex):
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

            self._handlers.append(wrapper)

            return wrapper

        return decorator


class Parser(object):
    TIME_RE = r'(?: \((\d+) ms(?: total)?\))?'

    handler = LineHandler()

    def __init__(self, output):
        self.output = output

        self.total_test_count = 0
        self.total_test_case_count = 0
        self.test_case_index = 0

        self.current_test_case = None
        self.current_test_count = 0
        self.current_test = None
        self.test_index = 0
        self.current_fail_count = 0

    def process(self, line):
        if not self.handler.process(self, line):
            self.output.raw_output(self.current_test, line)

    @staticmethod
    def parse_time(time):
        if time is not None:
            return int(time)
        else:
            return None

    @handler.add(r'Running (\d+) tests? from (\d+) test cases?')
    def start(self, total_test_count, total_test_case_count):
        self.total_test_count = int(total_test_count)
        self.total_test_case_count = int(total_test_case_count)
        self.is_summarizing_failures = False

    @handler.add(r'(\d+) tests? from (\d+) test cases? ran. ?' + TIME_RE + '$')
    def finish(self, total_test_count, total_test_case_count, time):
        self.output.finish(self.parse_time(time))

    @handler.add(r'\[ *PASSED *\] (\d+) tests?')
    def summary_passed(self, passed_test_count):
        pass

    @handler.add(r'\[ *FAILED *\] (\d+) tests?, listed below')
    def summary_failed1(self, failed_test_count):
        self.is_summarizing_failures = True
        pass

    @handler.add(r'(\d+) FAILED TESTS?')
    def summary_failed2(self, failed_test_count):
        pass

    @handler.add(r'YOU HAVE (\d+) DISABLED TESTS?')
    def summary_disabled(self, disabled_test_count):
        pass

    @handler.add(r'\[-+\] (\d+) tests? from (.*?)(?:, where (.*?))?' + TIME_RE + '$')
    def start_stop_test_case(self, test_count, test_case, where=None, time=None):

        self.current_test = None
        if not self.current_test_case:
            self.current_test_case = test_case
            self.current_test_count = int(test_count)
            self.current_fail_count = 0
            self.test_index = 0
            self.test_case_index += 1

            self.output.start_test_case(
                test_case, self.test_case_index, self.total_test_case_count, where)
        else:
            self.output.stop_test_case(
                test_case, self.test_case_index, self.total_test_case_count,
                self.current_test_count, self.current_fail_count, self.parse_time(time))
            self.current_test_case = None

    @handler.add(r'\[ *RUN *\] (.*)\.(.*)')
    def start_test(self, test_case, test):
        self.current_test = None
        self.test_index += 1
        self.output.start_test(test_case, test, self.test_index, self.current_test_count)

    @handler.add(r'\[ *(OK|FAILED) *\] (.*)\.(.*?)' + TIME_RE + '$')
    def stop_test(self, status, test_case, test, time=None):
        if self.is_summarizing_failures:
            return

        self.current_test = None
        if status == 'FAILED':
            self.current_fail_count += 1
        self.output.stop_test(
            status, test_case, test, self.test_index, self.current_test_count, self.parse_time(time))

    @handler.add(r'Global test environment set-up')
    def global_setup(self):
        self.output.global_setup(self.total_test_case_count)

    @handler.add(r'Global test environment tear-down')
    def global_teardown(self):
        self.output.global_teardown()

    @handler.add(r'^$')
    def blank_line(self):
        if self.current_test_case:
            # Within a test, return False so it's treated as raw output.
            return False


class ListOutput(object):
    def __init__(self, characters=UnicodeCharacters, print_time=0):
        self.characters = characters
        self.print_time = print_time

        # Internal state
        self.needs_newline = False
        self.current_test_case_has_raw = False
        self.max_line_len = 0
        self.progress_len = 0

        self.current_test_output = []
        self.failed_test_output = OrderedDict()

        # Test progress - provided to start_test_case and stored for use in
        # start_test
        self.test_case_index = None
        self.total_test_case_count = None

    def progress(self, current, total):
        total = str(total)
        return '%*i / ' % (len(total), current) + total

    def space_for_progress(self, current, total):
        return ' ' * len(self.progress(current, total))

    def time_details(self, time):
        if time is not None and time >= self.print_time:
            return ' (%s ms)' % time
        else:
            return ''

    def print_line(self, test_case, test_case_index, total_test_case_count, character,
                   color=None, details=None, force_progress=False):
        if self.needs_newline:
            print('\r', end='')
        else:
            self.max_line_len = 0

        color_len = 0

        if test_case_index is None:
            line = ' ' * self.progress_len
        elif self.needs_newline or force_progress:
            line = self.progress(test_case_index, total_test_case_count)
            self.progress_len = len(line)
        else:
            line = self.space_for_progress(test_case_index, total_test_case_count)
            self.progress_len = len(line)

        if color:
            line += color
            color_len += len(color)
        line += ' ' + character + ' ' + test_case
        if color:
            line += Style.RESET_ALL
            color_len += len(color)
        if details:
            line += details

        line_len = len(line) - color_len
        self.max_line_len = max(self.max_line_len, line_len)
        line += ' ' * (self.max_line_len - line_len)

        print(line, end='')
        self.needs_newline = True

    def raw_output(self, test, line):
        self.current_test_case_has_raw = True
        if self.needs_newline:
            print()
            self.needs_newline = False

        # Line is already newline-terminated, so use end=''
        print(line, end='')

        self.current_test_output.append(line)

    def start_test_case(self, test_case, test_case_index, total_test_case_count, where=None):
        self.print_line(test_case, test_case_index, total_test_case_count,
                        self.characters.empty, Fore.BLUE, force_progress=True)

        self.test_case_index = test_case_index
        self.total_test_case_count = total_test_case_count
        self.current_test_case_has_raw = False

    def stop_test_case(self, test_case, test_case_index, total_test_case_count,
                       test_count, fail_count, time=None):
        time_details = self.time_details(time)
        if not fail_count:
            self.print_line(test_case, test_case_index, total_test_case_count,
                            self.characters.success, Fore.GREEN, details=time_details)
        else:
            self.print_line(test_case, test_case_index, total_test_case_count,
                            self.characters.fail, Fore.RED,
                            ' - %i/%i failed%s' % (fail_count, test_count, time_details))

        print()
        self.needs_newline = False

    def start_test(self, test_case, test, test_index, test_count):
        # Print the count if this is still the first line of the test case.
        # If any raw output (including test failure messages) has occurred,
        # then it's not.
        if self.current_test_case_has_raw:
            test_case_index = None
            total_test_case_count = None
        else:
            test_case_index = self.test_case_index
            total_test_case_count = self.total_test_case_count

        self.print_line(test_case + '.' + test, test_case_index, total_test_case_count,
                        self.characters.empty, Fore.BLUE)

        self.current_test_output = []

    def stop_test(self, status, test_case, test, test_index, test_count, time=None):
        if status == 'FAILED':
            self.print_line(test_case + '.' + test, None, None,
                            self.characters.fail, Fore.RED)
            print()
            self.needs_newline = False
            self.failed_test_output[test_case + '.' + test] = self.current_test_output

    def global_setup(self, total_test_case_count):
        self.total_total_test_case_count = total_test_case_count
        self.print_line('Setup', None, None, self.characters.empty)

    def global_teardown(self):
        self.print_line('Teardown', None, None, self.characters.empty)

    def finish(self, time):
        self.print_line('Finished', None, None, self.characters.empty, details=self.time_details(time))
        print()
        self.needs_newline = False

        if self.failed_test_output:
            print()
            print(Fore.RED + 'FAILED TESTS:' + Style.RESET_ALL)
            for test_and_case, output in self.failed_test_output.items():
                print(Fore.RED + self.characters.fail + ' ' + test_and_case + Style.RESET_ALL)
                for line in output:
                    print('    ' + line, end='')


def get_output_kwargs():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--ascii', action='store_true',
                           help='Use ASCII progress / status, not Unicode')
    argparser.add_argument('--print_time', type=int, default=100,
                           help='Only print times that are at least N milliseconds')
    args = argparser.parse_args()

    output_kwargs = {}
    if args.ascii:
        output_kwargs['characters'] = AsciiCharacters
    output_kwargs['print_time'] = args.print_time

    return output_kwargs


def main():
    parser = Parser(ListOutput(**get_output_kwargs()))

    for line in sys.stdin:
        parser.process(line)


if __name__ == '__main__':
    main()
