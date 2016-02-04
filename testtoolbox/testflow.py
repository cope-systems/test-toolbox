import inspect
import textwrap
import traceback
from functools import wraps, partial

from testtoolbox.output import DefaultOutputFunctions


def should(behavior):
    return "should %s" % behavior


def must(behavior):
    return "must %s" % behavior


class TestNotImplemented(Exception):
    pass


class IgnoreTest(Exception):
    pass


def wrap_text_cleanly(text, width=120, preserve_newlines=False, initial_indent='', subsequent_indent='\t\t'):
    text_units = text.split('\n') if preserve_newlines else [text]
    wrap_function = partial(textwrap.wrap, width=width, initial_indent=initial_indent,
                            subsequent_indent=subsequent_indent)
    cleaned_text_units = map(wrap_function, text_units)
    return "\n".join([line for text_unit in cleaned_text_units for line in text_unit])


def _test_method_decorator_constructor(prefix, subject, predicate, width=120, print_method_docstring=True,
                                       docstring_indent=' ', suppress_traceback=False,
                                       output_functions=DefaultOutputFunctions):
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            output_functions.info(wrap_text_cleanly("%s%s %s" % (prefix, subject, predicate), width=width))
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
                output_msg = "Result: [IGNORED] %s" % ignore_msg
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
                if print_class_docstring and inspect.getdoc(old_class):
                    output_functions.info(wrap_text_cleanly(inspect.getdoc(old_class), preserve_newlines=True,
                                                            initial_indent=docstring_indent))
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

    def __init__(self, level_bullet="->", max_width=120, indent_str="   ", output_functions=DefaultOutputFunctions):
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
