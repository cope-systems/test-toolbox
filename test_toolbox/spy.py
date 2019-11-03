import inspect
from functools import update_wrapper
from types import MethodType, FunctionType, BuiltinFunctionType
from collections import namedtuple
from itertools import islice
import sys

IS_PY2 = sys.version_info[0] == 2
_REPR_MAX_WIDTH = [5000]


def set_reporting_max_width(w):
    """
    Set the max width for reported parameters. This is used to that failures don't overflow
    terminals in the event arguments are dumped.

    :param w: The new max width to enforce for the module
    :type w: int
    :return: True
    """
    _REPR_MAX_WIDTH[0] = int(w)
    return True


def get_reporting_max_width():
    """
    Get the current max width for reported parameters used in the Spy module.

    :return: The current reported max width.
    :rtype: int
    """
    return _REPR_MAX_WIDTH[0]


def _max_length_repr(obj, max_width=None):
    max_width = max_width or _REPR_MAX_WIDTH[0]
    result_str = repr(obj)
    if len(result_str) > max_width:
        return result_str[:max_width-3] + "..."
    else:
        return result_str


TargetInvocation = namedtuple("TargetInvocation", ("args", "kwargs", "result"))


class Spy(object):
    """
    A Spy is an callable wrapper which intercepts the invocations and results of the
    wrapped function, method, or other callable in order to allow users to examine
    and verify how callables might be consumed by other code.

    :param target_func: A function of any arity that will be wrapped with by this Spy.
    :param is_method: True if this is wrapped an uninitialized method (i.e. in a class declaration), False otherwise.
    :param is_not_inspectable: True if this is a built-in (i.e. implemented in C) or is otherwise unable to be
        inspected by the "inspect" module, False otherwise.
    :param verbose: True if verbose reporting is desired, False otherwise.
    :returns: A new callable, which wraps target_func and may be used as a stand in.
    """
    def __init__(self, target_func, is_method=False, is_not_inspectable=False, verbose=True):
        self.target_func = target_func
        self.is_weird_py2_call_method = False

        if is_not_inspectable:
            self.target_func_argspec = inspect.ArgSpec((), 'args', 'kwargs', ())
            self.get_type = BuiltinFunctionType
        elif is_method:
            args, varargs, kwargs, defaults = inspect.getargspec(target_func)
            self.target_func_argspec = inspect.ArgSpec(args[1:], varargs, kwargs, defaults)
            self.get_type = MethodType
        elif isinstance(target_func, FunctionType):
            self.target_func_argspec = inspect.getargspec(target_func)
            self.get_type = FunctionType
        elif isinstance(target_func, object) and callable(target_func):
            if IS_PY2:
                # I guess we just have to punt as Python 2 chokes on __call__ for getargspec.
                self.target_func_argspec = inspect.ArgSpec((), 'args', 'kwargs', ())
                self.is_weird_py2_call_method = True
            else:
                args, varargs, kwargs, defaults = inspect.getargspec(target_func.__call__)
                self.target_func_argspec = inspect.ArgSpec(args[1:], varargs, kwargs, defaults)
                self.is_method = True
            self.get_type = MethodType
        else:
            assert False, "Incompatible function {0} used with Spy.".format(target_func)
        if not self.is_weird_py2_call_method:
            update_wrapper(self, target_func)
        self.is_method = is_method
        self.successful_invocations = []
        self.successful_results = []
        self.verbose = verbose
        # If this is a decorated instance method, we've probably got to reinitialize the Spy
        # the first time it gets accessed (such that each instance has it's own Spy per method
        # per instance). To do this, we have to bootstrap new a new spy on first access (when
        # needs_reinit is likely set).
        self.needs_reinit = False

    def __call__(self, *args, **kwargs):
        result = self.target_func(*args, **kwargs)
        if self.is_method:
            self.successful_invocations.append(TargetInvocation(args[1:], kwargs, result))
        else:
            self.successful_invocations.append(TargetInvocation(args, kwargs, result))
        return result

    def __get__(self, instance, owner):
        if instance and self.needs_reinit:
            if IS_PY2:
                reinitialized = self.get_type(Spy(self.target_func, is_method=True), instance, owner)
            else:
                reinitialized = self.get_type(Spy(self.target_func, is_method=True), instance)
            setattr(instance, self.target_func.__name__, reinitialized)
            return reinitialized
        else:
            if IS_PY2:
                return self.get_type(self, instance, owner)
            else:
                return self.get_type(self, instance)

    @property
    def num_invocations(self):
        """
        Access the number of successful invocations recorded.

        :return: The integer number of invocations the Spy knows about.
        """
        return len(self.successful_invocations)

    def check_quantified_exact_match(self, times_predicate, *args, **kwargs):
        """
        Check to see if an exact match exists for the given times invoked predicate and argument matcher predicate.
        If there are unmatched arguments, this will return false.

        :param times_predicate: An arity 2 predicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this predicate.
        :param args: The predicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The predicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: True if a match/matches was found that satisfies all of the predicates, False otherwise.
        """
        def check_invocation(invocation_data):
            call_args, call_kwargs, _ = invocation_data
            return _calculate_match(self.target_func_argspec, args, kwargs, call_args, call_kwargs, exact=True)
        return times_predicate(
            [invoc_matched for invoc_matched in map(check_invocation, self.successful_invocations) if invoc_matched],
            self.successful_invocations
        )

    def check_quantified_partial_match(self, times_predicate, *args, **kwargs):
        """
        Check to see if an partial match exists for the given times invoked predicate and argument matcher predicate.
        Arguments that do no have corresponding matcher predicates are ignored.

        :param times_predicate: An arity 2 predicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this predicate.
        :param args: The predicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The predicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: True if a match/matches was found that satisfies all of the predicates, False otherwise.
        """
        def check_invocation(invocation_data):
            call_args, call_kwargs, _ = invocation_data
            return _calculate_match(self.target_func_argspec, args, kwargs, call_args, call_kwargs, exact=False)
        return times_predicate(
            [invoc_matched for invoc_matched in map(check_invocation, self.successful_invocations) if invoc_matched],
            self.successful_invocations
        )

    def check_quantified_result_match(self, times_predicate, result_predicate):
        """
        Check the spied results of all of the callable invocations, see if any match the specified predicates.

        :param times_predicate: An arity 2 predicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this predicate.
        :param result_predicate: An arity 1 predicate to match against the recorded result of a function call.
        :return: True if a result/results were found that satisfy both predicates.
        """
        successful_results = map(lambda o: o[2], self.successful_invocations)
        return times_predicate(map(result_predicate, successful_results))

    def check_quantified_partial_plus_result_match(self, times_predicate, result_predicate, *args, **kwargs):
        """
        Check the spied results of all of the callable invocations, see if any match satisfies the number of
        times predicate, the result predicate and the given partial invocation args/kwargs predicates.

        :param times_predicate: An arity 2 predicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this predicate.
        :param result_predicate: An arity 1 predicate to match against the recorded result of a function call.
        :param args: The predicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The predicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: True all of the predicates satisfied, False otherwise.
        """
        def check_invocation(invocation_data):
            call_args, call_kwargs, result = invocation_data
            params_match = _calculate_match(
                self.target_func_argspec, args, kwargs, call_args, call_kwargs, exact=False
            )
            result_matches = result_predicate(result)
            return params_match and result_matches
        return times_predicate(
            [invoc_matched for invoc_matched in map(check_invocation, self.successful_invocations) if invoc_matched],
            self.successful_invocations
        )

    def check_quantified_exact_plus_result_match(self, times_predicate, result_predicate, *args, **kwargs):
        """
        Check the spied results of all of the callable invocations, see if any match satisfies the number of
        times predicate, the result predicate and the given exact invocation args/kwargs predicates.

        :param times_predicate: An arity 2 predicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this predicate.
        :param result_predicate: An arity 1 predicate to match against the recorded result of a function call.
        :param args: The predicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The predicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: True all of the predicates satisfied, False otherwise.
        """

        def check_invocation(invocation_data):
            call_args, call_kwargs, result = invocation_data
            params_match = _calculate_match(
                self.target_func_argspec, args, kwargs, call_args, call_kwargs, exact=True
            )
            result_matches = result_predicate(result)
            return params_match and result_matches

        return times_predicate(
            [invoc_matched for invoc_matched in map(check_invocation, self.successful_invocations) if invoc_matched],
            self.successful_invocations
        )

    def assert_quantified_exact_match(self, times_predicate, *args, **kwargs):
        """
        Assert that an exact match exists for the given times invoked predicate and argument matcher predicate.
        If there are unmatched arguments, this will return false.

        :param times_predicate: An arity 2 predicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this predicate.
        :param args: The predicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The predicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: None.
        :raises: AssertionError on failure to match.
        """
        result = self.check_quantified_exact_match(times_predicate, *args, **kwargs)
        if not result and not self.verbose:
            raise AssertionError("Failed to find a matching exact invocation!")
        elif not result:
            raise AssertionError(
                "Failed to find a matching partial invocation!\n"
                "All invocations:\n[{}]".format(",\n".join(map(_max_length_repr, self.successful_invocations)))
            )

    def assert_quantified_partial_match(self, times_predicate, *args, **kwargs):
        """
        Assert that an partial match exists for the given times invoked predicate and argument matcher predicate.
        Arguments that do no have corresponding matcher predicates are ignored.

        :param times_predicate: An arity 2 predicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this predicate.
        :param args: The predicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The predicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: None.
        :raises: AssertionError on failure to match.
        """
        result = self.check_quantified_partial_match(times_predicate, *args, **kwargs)
        if not result and not self.verbose:
            raise AssertionError("Failed to find a matching partial invocation!")
        elif not result:
            raise AssertionError(
                "Failed to find a matching partial invocation!\n"
                "All invocations:\n[{}]".format(",\n".join(map(_max_length_repr, self.successful_invocations)))
            )

    def assert_quantified_result_match(self, times_predicate, result_predicate):
        """
        Assert the spied results of all of the callable invocations, see if any match the specified predicates.

        :param times_predicate: An arity 2 predicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this predicate.
        :param result_predicate: An arity 1 predicate to match against the recorded result of a function call.
        :return: None.
        :raises: AssertionError on failure to match.
        """
        result = self.check_quantified_result_match(times_predicate, result_predicate)
        if not result and not self.verbose:
            raise AssertionError("Failed to find a matching result!")
        elif not result:
            raise AssertionError(
                "Failed to find a matching result!\n"
                "All invocation results:\n[{}]".format(",\n".join(map(_max_length_repr, self.successful_results)))
            )

    def assert_quantified_partial_plus_result_match(self, times_predicate, result_predicate, *args, **kwargs):
        """
        Assert over the spied results of all of the callable invocations, see if any match satisfies the number of
        times predicate, the result predicate and the given partial invocation args/kwargs predicates.

        :param times_predicate: An arity 2 predicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this predicate.
        :param result_predicate: An arity 1 predicate to match against the recorded result of a function call.
        :param args: The predicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The predicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: None
        :raises: AssertionError on failure to match.
        """
        result = self.check_quantified_partial_plus_result_match(times_predicate, result_predicate, *args, **kwargs)
        if not result and not self.verbose:
            raise AssertionError("Failed to find a matching result!")
        elif not result:
            raise AssertionError(
                "Failed to find a matching result!\n"
                "All invocation results:\n[{}]".format(",\n".join(map(_max_length_repr, self.successful_results)))
            )

    def assert_quantified_exact_plus_result_match(self, times_predicate, result_predicate, *args, **kwargs):
        """
        Assert over the spied results of all of the callable invocations, see if any match satisfies the number of
        times predicate, the result predicate and the given exact invocation args/kwargs predicates.

        :param times_predicate: An arity 2 predicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this predicate.
        :param result_predicate: An arity 1 predicate to match against the recorded result of a function call.
        :param args: The predicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The predicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: None
        :raises: AssertionError on failure to match.
        """

        result = self.check_quantified_exact_plus_result_match(times_predicate, result_predicate, *args, **kwargs)
        if not result and not self.verbose:
            raise AssertionError("Failed to find a matching result!")
        elif not result:
            raise AssertionError(
                "Failed to find a matching result!\n"
                "All invocation results:\n[{}]".format(",\n".join(map(_max_length_repr, self.successful_results)))
            )

    def assert_any_exact_match(self, *args, **kwargs):
        """
        Wraps assert_quantified_exact_match, seeing if the specified arguments show up at least once.

        :param args: The arguments to attempt to match on.
        :param kwargs: The keyword arguments to match on.
        :return: None
        :raises: AssertionError on failure to match.
        """
        self.assert_quantified_exact_match(at_least_once, *args, **kwargs)

    def assert_one_exact_match(self, *args, **kwargs):
        """
        Wraps assert_quantified_exact_match, seeing if the specified arguments show up exactly once.

        :param args: The arguments to attempt to match on.
        :param kwargs: The keyword arguments to match on.
        :return: None
        :raises: AssertionError on failure to match.
        """
        self.assert_quantified_exact_match(once, *args, **kwargs)

    def assert_all_exact_match(self, *args, **kwargs):
        """
        Wraps assert_quantified_exact_match, seeing if the specified arguments always appear.

        :param args: The arguments to attempt to match on.
        :param kwargs: The keyword arguments to match on.
        :return: None
        :raises: AssertionError on failure to match.
        """
        self.assert_quantified_exact_match(always, *args, **kwargs)

    def assert_any_partial_match(self, *args, **kwargs):
        """
        Wraps assert_quantified_partial_match, seeing if the specified arguments show up at least once.

        :param args: The arguments to attempt to match on.
        :param kwargs: The keyword arguments to match on.
        :return: None
        :raises: AssertionError on failure to match.
        """
        self.assert_quantified_partial_match(at_least_once, *args, **kwargs)

    def assert_one_partial_match(self, *args, **kwargs):
        """
        Wraps assert_quantified_partial_match, seeing if the specified arguments show up exactly once.

        :param args: The arguments to attempt to match on.
        :param kwargs: The keyword arguments to match on.
        :return: None
        :raises: AssertionError on failure to match.
        """
        self.assert_quantified_partial_match(once, *args, **kwargs)

    def assert_all_partial_match(self, *args, **kwargs):
        """
        Wraps assert_quantified_partial_match, seeing if the specified arguments always show up.

        :param args: The arguments to attempt to match on.
        :param kwargs: The keyword arguments to match on.
        :return: None
        :raises: AssertionError on failure to match.
        """
        self.assert_quantified_partial_match(always, *args, **kwargs)

    def assert_any_result_match(self, result_predicate):
        """
        Wraps assert_quantified_partial_match, seeing if the result predicate returns true at least once.

        :param result_predicate: The function to match against stored results.
        :return: None
        :raises: AssertionError on failure to match.
        """
        self.assert_quantified_result_match(at_least_once, result_predicate)

    def assert_one_result_match(self, result_predicate):
        """
        Wraps assert_quantified_partial_match, seeing if the result predicate is true exactly once.

        :param result_predicate: The function to match against stored results.
        :return: None
        :raises: AssertionError on failure to match.
        """
        self.assert_quantified_result_match(once, result_predicate)

    def assert_all_result_match(self, result_predicate):
        """
        Wraps assert_quantified_partial_match, seeing if the result predicate is always true.

        :param result_predicate: The function to match against stored results.
        :return: None
        :raises: AssertionError on failure to match.
        """
        self.assert_quantified_result_match(always, result_predicate)

    def reset(self):
        """
        Clear all of the recorded invocations to return to an "uninvoked" state.

        :return: True
        """
        self.successful_invocations = []
        self.successful_results = []
        return True


def _align_args_kwargs_to_argspec_args(argspec_args, args, kwargs):
    aligned_map = dict(zip(argspec_args[:len(args)], args))
    aligned_map.update((k, v) for k, v in kwargs.items() if k in argspec_args)
    return aligned_map


def _apply_predicate_map_to_value_map(predicate_map, value_map):
    for key in set(predicate_map.keys()):
        yield predicate_map[key](value_map[key])


def _apply_predicate_list_to_value_list(predicate_list, value_list):
    for predicate, value in islice(zip(predicate_list, value_list), 0, len(predicate_list)):
        yield predicate(value)


def _calculate_match(argspec, predicate_args, predicate_kwargs, call_args, call_kwargs, exact=True):
    if argspec.defaults:
        aligned_call_args = dict(zip(argspec.args[len(argspec.defaults)+1::-1], argspec.defaults[::-1]))
    else:
        aligned_call_args = {}
    aligned_call_args.update(_align_args_kwargs_to_argspec_args(argspec.args, call_args, call_kwargs))
    aligned_predicate_args = _align_args_kwargs_to_argspec_args(argspec.args, predicate_args, predicate_kwargs)

    extra_call_args = call_args[len(argspec.args):]
    extra_predicate_args = predicate_args[len(argspec.args):]

    extra_call_kwargs = dict((k, v) for k, v in call_kwargs.items() if k not in aligned_call_args)
    extra_predicate_kwargs = dict((k, v) for k, v in predicate_kwargs.items() if k not in aligned_predicate_args)

    if exact:
        matching_named_call_args = set(aligned_call_args.keys()) == set(aligned_predicate_args.keys())
        matching_extra_args = len(extra_call_args) == len(extra_predicate_args)
        matching_extra_kwargs = set(extra_call_kwargs.keys()) == set(extra_predicate_kwargs.keys())
    else:
        matching_named_call_args = set(aligned_call_args.keys()) >= set(aligned_predicate_args.keys())
        matching_extra_args = len(extra_call_args) >= len(extra_predicate_args)
        matching_extra_kwargs = set(extra_call_kwargs.keys()) >= set(extra_predicate_kwargs.keys())

    if matching_named_call_args and matching_extra_args and matching_extra_kwargs:
        all_named_pass = all(_apply_predicate_map_to_value_map(aligned_predicate_args, aligned_call_args))
        all_extra_args_pass = all(_apply_predicate_list_to_value_list(extra_predicate_args, extra_call_args))
        all_extra_kwargs_pass = all(_apply_predicate_map_to_value_map(extra_predicate_kwargs, extra_call_kwargs))
        return all_named_pass and all_extra_args_pass and all_extra_kwargs_pass
    else:
        return False


def times(num_times):
    """
    Create a predicate that checks to see if the number of matching invocations occur exactly the specified number
    of times.

    :param num_times: The exact number of matches that must have occurred.
    :return: A predicate to check the resulting matching invocations list.
    """
    def predicate(matching_invocations, _):
        return len(matching_invocations) == num_times
    return predicate


once = times(1)
never = times(0)


def at_least_times(num_times):
    """
    Create a predicate that checks to see if the number of matching invocations occur at least the specified number
    of times.

    :param num_times: The minimum number of matches that must have occurred.
    :return: A predicate to check the resulting matching invocations list.
    """
    def predicate(matching_invocations, _):
        return len(matching_invocations) >= num_times
    return predicate


at_least_once = at_least_times(1)


def always(matching_invocations, all_invocations):
    """
    This predicate verifies that all invocations must have matched.

    :param matching_invocations: All found matching invocations.
    :param all_invocations: All invocations of the Spy
    :return: True or False.
    """
    return len(matching_invocations) == len(all_invocations)


def apply_builtin_function_spy(func):
    """
    Apply a spy to a built-in function that does not work with inspect.getargspec.

    :param func: The function to spy on.
    :return: The function with a spy attached.
    """
    return Spy(func, is_not_inspectable=True)


def apply_function_spy(func):
    """
    Apply a Spy to a function, lambda, staticmethod, or instantiated object's method.

    :param func: The callable to spy on.
    :return: The callable with attached spy.
    """
    return Spy(func)


def apply_method_spy(method):
    """
    Apply a spy to an instance method declaration on an object. This must be handled differently because
    of the way Python handles decorators and does virtual method dispatch on instance methods.

    :param method: The instance method (or possibly classmethod) to spy on.
    :return: The method with attached spy.
    """
    new_spy = Spy(method, is_method=True)
    new_spy.needs_reinit = True
    return new_spy


def anything(_):
    """
    This predicate will always return True, and thus matches anything.

    :param _: The argument, which is ignored.
    :return: True
    """
    return True


def any_of(elements):
    """
    Check to see if the argument is contained in a list of possible elements.

    :param elements: The elements to check the argument against in the predicate.
    :return: A predicate to check if the argument is a constituent element.
    """
    def predicate(argument):
        return argument in elements
    return predicate


def equal_to(element):
    """
    Check to see if the argument is equal to the specified element

    :param element: The element to check against the argument.
    :return: A predicate to check if the argument is equal to the element.
    """
    def predicate(argument):
        return argument == element
    return predicate


def contains(element):
    """
    Check to see if an argument contains a specified element.

    :param element: The element to check against.
    :return: A predicate to check if the argument is equal to the element.
    """
    def predicate(argument):
        try:
            return element in argument
        except:
            return False
    return predicate


def identical_to(element):
    """
    Check to see if the argument is identical to the specified element

    :param element: The element to check against the argument.
    :return: A predicate to check if the argument is identical to the element.
    """
    def predicate(argument):
        return element is argument
    return predicate


def instance_of(cls):
    """
    Check to see if the argument is an instance of the specified class element.

    :param cls: The element to use to check inheritance of the argument.
    :return: A predicate to check if the argument an instance of the element.
    """
    def predicate(argument):
        return isinstance(argument, cls)
    return predicate
