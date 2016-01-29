from __future__ import print_function
from functools import wraps, partial
from collections import namedtuple
import traceback
import inspect
import textwrap
import time
import ctypes

__author__ = 'Robert Cope'


class ANSITermCodes(object):
    WHITE = '\033[37m'
    CYAN = '\033[36m'
    PURPLE = '\033[35m'
    BLUE = '\033[34m'
    YELLOW = '\033[33m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    BLACK = '\033[30m'
    NORMAL_COLOR = '\033[39m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    HALF_BRIGHT = '\033[1m'
    NORMAL_BRIGHT = '\033[22m'
    UNDERLINE = '\033[4m'
    UNDERLINE_OFF = '\033[24m'
    BLINK = '\033[5m'
    BLINK_OFF = '\033[25m'


def _output_formatter(output_code, text, terminator_code=ANSITermCodes.RESET):
    return "%s%s%s" % (output_code, str(text), terminator_code)


purple = partial(_output_formatter, ANSITermCodes.PURPLE, terminator_code=ANSITermCodes.NORMAL_COLOR)
green = partial(_output_formatter, ANSITermCodes.GREEN, terminator_code=ANSITermCodes.NORMAL_COLOR)
red = partial(_output_formatter, ANSITermCodes.RED, terminator_code=ANSITermCodes.NORMAL_COLOR)
yellow = partial(_output_formatter, ANSITermCodes.YELLOW, terminator_code=ANSITermCodes.NORMAL_COLOR)
blue = partial(_output_formatter, ANSITermCodes.BLUE, terminator_code=ANSITermCodes.NORMAL_COLOR)
cyan = partial(_output_formatter, ANSITermCodes.CYAN, terminator_code=ANSITermCodes.NORMAL_COLOR)
black = partial(_output_formatter, ANSITermCodes.BLACK, terminator_code=ANSITermCodes.NORMAL_COLOR)
white = partial(_output_formatter, ANSITermCodes.WHITE, terminator_code=ANSITermCodes.NORMAL_COLOR)
bold = partial(_output_formatter, ANSITermCodes.BOLD, terminator_code=ANSITermCodes.NORMAL_BRIGHT)
half_bright = partial(_output_formatter, ANSITermCodes.HALF_BRIGHT, terminator_code=ANSITermCodes.NORMAL_BRIGHT)
underline = partial(_output_formatter, ANSITermCodes.UNDERLINE, terminator_code=ANSITermCodes.UNDERLINE_OFF)
blinking = partial(_output_formatter, ANSITermCodes.BLINK, terminator_code=ANSITermCodes.BLINK_OFF)


def _print_formatter(color_str, *args):
    args = args + (ANSITermCodes.RESET,)
    print(color_str, *args)


print_purple = partial(_print_formatter, ANSITermCodes.PURPLE)
print_green = partial(_print_formatter, ANSITermCodes.GREEN)
print_red = partial(_print_formatter, ANSITermCodes.RED)
print_yellow = partial(_print_formatter, ANSITermCodes.YELLOW)
print_cyan = partial(_print_formatter, ANSITermCodes.CYAN)
print_blue = partial(_print_formatter, ANSITermCodes.BLUE)
print_black = partial(_print_formatter, ANSITermCodes.BLACK)
print_white = partial(_print_formatter, ANSITermCodes.WHITE)
print_bold = partial(_print_formatter, ANSITermCodes.BOLD)
print_half_bright = partial(_print_formatter, ANSITermCodes.HALF_BRIGHT)
print_underline = partial(_print_formatter, ANSITermCodes.UNDERLINE)
print_blinking = partial(_print_formatter, ANSITermCodes.BLINK)


TestOutputFunctions = namedtuple("TestOutputFunctions", ["pass_", "ignore", "warn", "fail"])
DefaultOutputFunctions = TestOutputFunctions(print_green, print_green, print_yellow, print_red)


def should(behavior):
    return "should %s" % behavior


def must(behavior):
    return "must %s" % behavior


class TestNotImplemented(Exception):
    pass


class IgnoreTest(Exception):
    pass


def wrap_text_cleanly(text, width=80):
    lines = textwrap.wrap(text, width=width, subsequent_indent='\t\t')
    return "\n".join(lines)


def _test_method_decorator_constructor(prefix, subject, predicate, width=80, output_functions=DefaultOutputFunctions,
                                       suppress_traceback=False):
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            try:
                ret_val = func(*args, **kwargs)
                output_functions.pass_(wrap_text_cleanly("[PASS] %s%s %s" % (prefix, subject, predicate), width=width))
                return ret_val
            except TestNotImplemented:
                output_msg = "[NOT IMPLEMENTED] %s%s %s" % (prefix, subject, predicate)
                output_functions.warn(wrap_text_cleanly(output_msg, width=width))
            except IgnoreTest as e:
                ignore_msg = "(%s)" % e.message if e.message else ""
                output_msg = "[IGNORED] %s%s %s (%s)" % (prefix, subject, predicate, ignore_msg)
                output_functions.warn(wrap_text_cleanly(output_msg, width=width))
            except Exception:
                output_functions.fail(wrap_text_cleanly("[FAIL] %s should %s" % (subject, predicate), width=width))
                if not suppress_traceback:
                    output_functions.fail(traceback.format_exc())
                raise
        return decorated
    return decorator

case_descriptor = partial(_test_method_decorator_constructor, "")
unit_descriptor = partial(_test_method_decorator_constructor, "")
scenario_descriptor = partial(_test_method_decorator_constructor, "Scenario: ")
feature_descriptor = partial(_test_method_decorator_constructor, "Feature: ")


def ignore_test(reason=""):
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            raise IgnoreTest(reason)

        return decorated

    return decorator


def _test_case_class_decorator_constructor(prefix, name, print_class_docstring=True, width=80,
                                           output_functions=DefaultOutputFunctions):
    output_str = "%s%s" % (prefix, name)

    def decorator(old_class):
        class WrappedClass(old_class):
            @classmethod
            def setUpClass(cls):
                output_functions.pass_("-" * width)
                output_functions.pass_(wrap_text_cleanly(output_str, width=width))
                output_functions.pass_("-" * width)
                if print_class_docstring:
                    output_functions.pass_(wrap_text_cleanly(inspect.getdoc(old_class)))
                old_class.setUpClass()

        return WrappedClass

    return decorator

case_name = partial(_test_case_class_decorator_constructor, "")
feature = partial(_test_case_class_decorator_constructor, "Feature: ")
scenario = partial(_test_case_class_decorator_constructor, "Scenario: ")


class BDD(object):
    PASS = object()
    IGNORE = object()
    WARNING = object()
    FAIL = object()

    bdd_names = ['given', 'when', 'then', 'also', 'and_', 'but']

    class _Step(object):
        def __init__(self, level_name, parent):
            self.index = None
            self.level_name = level_name
            self.parent = parent
            self.text_description = ""
            self.warn_exeptions = []
            self.ignore_exceptions = []
            self.cleanup_func = lambda: True

        def __call__(self, text_description, warn_exceptions=None, ignore_exceptions=None, cleanup_func=lambda: True):
            self.text_description = text_description
            self.warn_exeptions = self.warn_exeptions if warn_exceptions is None else warn_exceptions
            self.ignore_exceptions = self.ignore_exceptions if ignore_exceptions is None else ignore_exceptions
            self.cleanup_func = cleanup_func
            return self

        def __getattr__(self, item):
            return self.parent.__getattr__(item)

        def __enter__(self):
            self.index = self.parent._enter_handler(self.level_name, self.text_description)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.cleanup_func()
            return self.parent._exit_handler(exc_type, exc_val, exc_tb, self.index,
                                             self.warn_exeptions, self.ignore_exceptions)

    def __init__(self, level_bullet="->", max_width=120, indent_str="  ", output_functions=DefaultOutputFunctions):
        self.level_bullet = level_bullet
        self.max_width = max_width
        self.indent_str = indent_str
        self.output_functions = output_functions
        self.current_level = 0
        self.current_index = 0
        self.entry_data = {}
        self.exit_data = {}

    def __getattr__(self, name):
        if name in self.bdd_names:
            return self._Step(name, self)
        else:
            raise AttributeError("No such attribute %s" % name)

    def _enter_handler(self, level_name, text_description):
        current_index, current_level = self.current_index, self.current_level
        self.current_index, self.current_level = current_index + 1, current_level + 1
        current_indent_str = (self.indent_str * self.current_level) + self.level_bullet
        cleaned_level_name = level_name.replace("_", " ").capitalize().strip()
        bdd_str = "%s %s %s" % (current_indent_str, cleaned_level_name, text_description)
        self.entry_data[current_index] = bdd_str
        return current_index

    def _exit_handler(self, exc_type, exc_val, _, step_index, warn_excs, ignore_excs):
        self.current_level -= 1
        if not exc_type:
            self.exit_data[step_index] = (self.PASS, None)
            result = True
        elif exc_type in ignore_excs:
            self.exit_data[step_index] = (self.IGNORE, repr(exc_val))
            result = True
        elif exc_type in warn_excs:
            self.exit_data[step_index] = (self.WARNING, repr(exc_val))
            result = True
        else:
            self.exit_data[step_index] = (self.FAIL, repr(exc_val))
            result = False
        if self.current_level == 0:
            self._print_steps()
            self.entry_data, self.exit_data, self.current_index = {}, {}, 0
        return result

    def _print_steps(self):
        wrap_text = partial(wrap_text_cleanly, width=self.max_width)
        for key in sorted(self.exit_data.iterkeys()):
            entry_data, exit_data = self.entry_data[key], self.exit_data[key]
            if exit_data[0] is self.PASS:
                self.output_functions.pass_(wrap_text(entry_data, width=self.max_width))
            elif exit_data[0] is self.IGNORE:
                strs = (entry_data, "(Ignored Exception: %s)" % exit_data[1])
                entry, exception_data = map(wrap_text, strs)
                formatted_str = "%s\n\t\t%s" % (entry, exception_data)
                self.output_functions.ignore(formatted_str)
            elif exit_data[0] is self.WARNING:
                strs = ("%s  **WARNING**" % entry_data, "(Exception: %s)" % exit_data[1])
                entry, exception_data = map(wrap_text, strs)
                formatted_str = "%s\n\t\t%s" % (entry, exception_data)
                self.output_functions.warn(formatted_str)
            elif exit_data[0] is self.FAIL:
                strs = ("%s **FAIL**" % entry_data, "(Exception: %s)" % exit_data[1])
                entry, exception_data = map(wrap_text, strs)
                formatted_str = "%s\n\t\t%s" % (entry, exception_data)
                self.output_functions.fail(formatted_str)


def modify_buffer_object(source_buffer, dest_buffer, nbytes=None):
    """
    Modify a python object that supports the buffer interface internally.
    This is useful for testing things like socket.recv_into()

    dest_buffer must be smaller than source_buffer, or the code will assert.

    :param source_buffer: The source for the new data to be written into dest_buffer.
    :param dest_buffer: The buffer to be modified inline.
    :param nbytes: (OPTIONAL) The maximum number of bytes to write into the dest_buffer.
        If set, the number of bytes written is the minimum of nbytes and the source length.
        Default: None
    :return: The total number of bytes written into dest_buffer.
    """
    assert len(source_buffer) < len(dest_buffer)
    copy_len = len(source_buffer) if nbytes is None else min(nbytes, source_buffer)
    buffer_ptr = (ctypes.c_byte * len(dest_buffer)).from_buffer(dest_buffer)
    new_value_ptr = (ctypes.c_byte * len(source_buffer)).from_buffer_copy(source_buffer)
    buffer_ptr[:copy_len] = new_value_ptr[:]
    return copy_len


def await_condition(description, condition_eval_callable, on_failure=lambda: True, timeout=10, poll_ms=100):
    """
    Await a condition function to return True, otherwise assert.

    :param description: A string description of the condition we are awaiting.
    :param condition_eval_callable: The callable of arity 0 (function, lambda, etc.) to monitor.
        This should return False when not completed, and return True when done.
    :param on_failure: (OPTIONAL) A callable of arity 0 that is called when a failure condition occurs.
        Default: NOOP
    :param timeout: (OPTIONAL) The number of seconds to wait for the condition to become True.
        Default: 10 s
    :param poll_ms: (OPTIONAL) The period of time between checking the condition.
        Default: 100 ms
    :return: None. Will raise an AssertionError if the condition did not return True in the allotted time.
    """
    poll_s = poll_ms / 1000.0
    start_time = time.time()

    def should_continue():
        return time.time() - start_time < timeout

    while not condition_eval_callable():
        if not should_continue():
            on_failure()
            raise AssertionError("Awaiting condition %s has timed out after %f seconds"
                                 "" % (str(description), float(timeout)))
        time.sleep(poll_s)
