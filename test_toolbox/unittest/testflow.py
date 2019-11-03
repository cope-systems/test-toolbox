import inspect
import traceback
from functools import partial, wraps
from unittest import SkipTest

from test_toolbox.output import DefaultOutputFunctions, wrap_text_cleanly


def should(behavior):
    return "should %s" % behavior


def must(behavior):
    return "must %s" % behavior


class TestNotImplemented(SkipTest):
    def __init__(self, reason="Test Not Implemented", *args, **kwargs):
        super(TestNotImplemented, self).__init__(reason, *args, **kwargs)


class IgnoreTest(SkipTest):
    def __init__(self, reason="Test Ignored", *args, **kwargs):
        super(IgnoreTest, self).__init__(reason, *args, **kwargs)


def _test_method_decorator_constructor(prefix, subject, predicate, width=120, print_method_docstring=True,
                                       docstring_indent=' ', suppress_traceback=False,
                                       output_functions=DefaultOutputFunctions):
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            output_functions.info(wrap_text_cleanly("{0}{1} {2}".format(prefix, subject, predicate), width=width))
            if print_method_docstring and inspect.getdoc(func):
                output_functions.info(wrap_text_cleanly(inspect.getdoc(func), preserve_newlines=True,
                                                        initial_indent=docstring_indent))
            try:
                ret_val = func(*args, **kwargs)
                output_functions.pass_(wrap_text_cleanly("Result: [PASS]", width=width))
                return ret_val
            except TestNotImplemented:
                output_msg = "Result: [NOT IMPLEMENTED]"
                output_functions.warn(wrap_text_cleanly(output_msg, width=width))
            except IgnoreTest as e:
                ignore_msg = "(%s)" % getattr(e, 'message') if getattr(e, 'message') else ""
                output_msg = "Result: [IGNORED] {0}".format(ignore_msg)
                output_functions.warn(wrap_text_cleanly(output_msg, width=width))
            except BaseException as e:
                output_functions.fail(wrap_text_cleanly("Result: [FAIL] %s" % repr(e), width=width))
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


def _test_case_class_decorator_constructor(prefix, name, print_class_docstring=True, docstring_indent=' ', width=120,
                                           output_functions=DefaultOutputFunctions):
    output_str = "%s%s" % (prefix, name)

    def decorator(old_class):
        class WrappedClass(old_class):
            @classmethod
            def setUpClass(cls):
                output_functions.info("-" * width)
                output_functions.info(wrap_text_cleanly(output_str, width=width))
                output_functions.info("-" * width)
                if print_class_docstring and getattr(old_class, '__doc__', None):
                    output_functions.info(wrap_text_cleanly(inspect.getdoc(old_class), preserve_newlines=True,
                                                            initial_indent=docstring_indent))
                old_class.setUpClass()

        return WrappedClass

    return decorator


case_name = partial(_test_case_class_decorator_constructor, "")
feature = partial(_test_case_class_decorator_constructor, "Feature: ")
scenario = partial(_test_case_class_decorator_constructor, "Scenario: ")
