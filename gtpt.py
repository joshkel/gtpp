#!/usr/bin/env python3

import colorama
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
            f(self, *m.groups())
            return True

        wrapper.is_handler = True

        return wrapper

    return decorator


class Parser(object):
    def __init__(self):
        members = [getattr(self, i) for i in dir(self)]
        self.handlers = [f for f in members if callable(f) and hasattr(f, 'is_handler')]

    def process(self, line):
        for h in self.handlers:
            if h(line):
                return True

    @handle(r'Running (\d+) tests? from (\d+) test cases?')
    def start(self, test_count, test_case_count):
        self.test_count = test_count
        self.test_case_count = test_case_count


def main():
    parser = Parser()

    for line in sys.stdin:
        if not parser.process(line):
            print(line, end='')


if __name__ == '__main__':
    main()
