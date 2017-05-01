# Google Test Pretty Printer

`gtpp` (Google Test Pretty Printer) is a pretty printer / test listener for
[Google Test](https://github.com/google/googletest).

Google Test is a great testing framework for C++. It has lots of powerful
features, good popularity, a fully functional mocking library that works with
it…

There's one problem. Google Test is *loud*.  `gtpp` makes it much more pleasant
to use.

[See these screenshots for an example.](docs/screenshots.md)

(`gtpp` is not a Google project. The author is not affiliated with Google.)

## Features

* Quieter output - By default, Google Test prints 2 lines of output per
  individual test, plus 3 lines for every test case.  `gtpp` prints one line
  per test case under normal operation, without sacrificing any detail if
  individual tests fail or need more detailed output.
* If even that's more verbose than you'd like, then use `--failures-only`, and
  only failing tests (or any test with actual output) will be left on the screen.
* Automatic verbosity - If test filtering is enabled, because you're trying to
  zero in on particular problems, `gtpp` automatically switches to more verbose
  output.
* Details of test failures - The list of failed tests at the end includes
  actual actual and expected values, instead of forcing you to scroll back up
  to find details on what went wrong.
* Smart time output - Google Test prints how long each test takes.  `gtpp`
  enhances this to only print interesting test cases' times (over 50 ms by
  default; configurable with `--print-time=N`), to help you focus on slow
  tests.
* Unicode output - because every test runner needs ✓ and ✗.  You can use the
  `--ascii` option to switch back to plain ASCII if your terminal doesn't
  support these characters.

## Usage

1. Clone the repository.

    ```
    git clone https://github.com/joshkel/gtpp.git
    ```

2. Install prerequisites.  For example, on Ubuntu:

    ```
    sudo apt-get install python3-colorama
    ```

    Or set up a virtualenv and install prerequisites there.

    ```
    cd gtpp
    python3 -m venv env
    . env/bin/activate
    pip install -r requirements.txt
    ```

3. Run your unit tests through `gtpp`. For example:

    ```
    path/to/gtpp.py ./test_suite [--gtest_args...]
    # Or
    path/to/gtpp.py make test
    ```

    Or run your tests normally and pipe the results through `gtpp`.  For example:

    ```
    make test |& path/to/gtpp.py
    ```

## Why Python?

Google Test provides its own [Event Listener
API](https://github.com/google/googletest/blob/master/googletest/docs/AdvancedGuide.md#extending-google-test-by-handling-test-events),
so why write an external program?  Partly for flexibility - this allows _any_
test suite that uses Google Test to work, without source modifications - and
partly for power - because the external program sees all of the output, it can
add features like including failing tests' full output at the end of the run.
