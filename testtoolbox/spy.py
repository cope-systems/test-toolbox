import inspect
from functools import update_wrapper
from types import MethodType, FunctionType, BuiltinFunctionType
from collections import namedtuple
from itertools import islice
import sys

IS_PY2 = sys.version_info[0] == 2


TargetInvocation = namedtuple("TargetInvocation", ("args", "kwargs", "result"))


class Spy(object):
    def __init__(self, target_func, is_method=False, is_not_inspectable=False, verbose=True):
        self.target_func = target_func
        if is_not_inspectable:
            self.target_func_argspec = inspect.ArgSpec((), 'args', 'kwargs', ())
            self.get_type = BuiltinFunctionType
        elif is_method:
            args, varargs, kwargs, defaults = inspect.getargspec(target_func)
            self.target_func_argspec = inspect.ArgSpec(args[1:], varargs, kwargs, defaults)
            self.get_type = MethodType
        else:
            self.target_func_argspec = inspect.getargspec(target_func)
            self.get_type = FunctionType
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

    def check_quantified_exact_match(self, times_praedicate, *args, **kwargs):
        """
        Check to see if an exact match exists for the given times invoked praedicate and argument matcher praedicate.
        If there are unmatched arguments, this will return false.
        :param times_praedicate: An arity 2 praedicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this praedicate.
        :param args: The praedicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The praedicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: True if a match/matches was found that satisfies all of the praedicates, False otherwise.
        """
        def check_invocation(invocation_data):
            call_args, call_kwargs, _ = invocation_data
            return _calculate_match(self.target_func_argspec, args, kwargs, call_args, call_kwargs, exact=True)
        return times_praedicate(
            [invoc_matched for invoc_matched in map(check_invocation, self.successful_invocations) if invoc_matched],
            self.successful_invocations
        )

    def check_quantified_partial_match(self, times_praedicate, *args, **kwargs):
        """
        Check to see if an partial match exists for the given times invoked praedicate and argument matcher praedicate.
        Arguments that do no have corresponding matcher praedicates are ignored.
        :param times_praedicate: An arity 2 praedicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this praedicate.
        :param args: The praedicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The praedicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: True if a match/matches was found that satisfies all of the praedicates, False otherwise.
        """
        def check_invocation(invocation_data):
            call_args, call_kwargs, _ = invocation_data
            return _calculate_match(self.target_func_argspec, args, kwargs, call_args, call_kwargs, exact=False)
        return times_praedicate(
            [invoc_matched for invoc_matched in map(check_invocation, self.successful_invocations) if invoc_matched],
            self.successful_invocations
        )

    def check_quantified_result_match(self, times_praedicate, result_praedicate):
        """
        Check the spied results of all of the callable invocations, see if any match the specified praedicates.
        :param times_praedicate: An arity 2 praedicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this praedicate.
        :param result_praedicate: An arity 1 praedicate to match against the recorded result of a function call.
        :return: True if a result/results were found that satisfy both praedicates.
        """
        successful_results = map(lambda o: o[2], self.successful_invocations)
        return times_praedicate(map(result_praedicate, successful_results))

    def assert_quantified_exact_match(self, times_praedicate, *args, **kwargs):
        """
        Assert that an exact match exists for the given times invoked praedicate and argument matcher praedicate.
        If there are unmatched arguments, this will return false.
        :param times_praedicate: An arity 2 praedicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this praedicate.
        :param args: The praedicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The praedicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: None. If the matches can not be satisfied, this raises an AssertionError.
        """
        result = self.check_quantified_exact_match(times_praedicate, *args, **kwargs)
        if not result and not self.verbose:
            raise AssertionError("Failed to find a matching exact invocation!")
        elif not result:
            raise AssertionError(
                "Failed to find a matching partial invocation!\n"
                "All invocations:\n[{}]".format(",\n".join(map(repr, self.successful_invocations)))
            )

    def assert_quantified_partial_match(self, times_praedicate, *args, **kwargs):
        """
        Assert that an partial match exists for the given times invoked praedicate and argument matcher praedicate.
        Arguments that do no have corresponding matcher praedicates are ignored.
        :param times_praedicate: An arity 2 praedicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this praedicate.
        :param args: The praedicate positional arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :param kwargs: The praedicate keyword arguments to match up against the call arguments, to check and verify
            against. These should all be arity 1 and return True/False.
        :return: None. If the matches can not be satisfied, this raises an AssertionError.
        """
        result = self.check_quantified_partial_match(times_praedicate, *args, **kwargs)
        if not result and not self.verbose:
            raise AssertionError("Failed to find a matching partial invocation!")
        elif not result:
            raise AssertionError(
                "Failed to find a matching partial invocation!\n"
                "All invocations:\n[{}]".format(",\n".join(map(repr, self.successful_invocations)))
            )

    def assert_quantified_result_match(self, times_praedicate, result_praedicate):
        """
        Assert the spied results of all of the callable invocations, see if any match the specified praedicates.
        :param times_praedicate: An arity 2 praedicate that takes the successful invocation list, and the total
            invocation list, returns true or false based on these matching number of times executed expectation
            embedded in this praedicate.
        :param result_praedicate: An arity 1 praedicate to match against the recorded result of a function call.
        :return: None. Will raise an AssertionError if no match was found.
        """
        result = self.check_quantified_result_match(times_praedicate, result_praedicate)
        if not result and not self.verbose:
            raise AssertionError("Failed to find a matching result!")
        elif not result:
            raise AssertionError(
                "Failed to find a matching result!\n"
                "All invocation results:\n[{}]".format(",\n".join(map(repr, self.successful_results)))
            )

    def assert_any_exact_match(self, *args, **kwargs):
        self.assert_quantified_exact_match(at_least_once, *args, **kwargs)

    def assert_one_exact_match(self, *args, **kwargs):
        self.assert_quantified_exact_match(once, *args, **kwargs)

    def assert_all_exact_match(self, *args, **kwargs):
        self.assert_quantified_exact_match(always, *args, **kwargs)

    def assert_any_partial_match(self, *args, **kwargs):
        self.assert_quantified_partial_match(at_least_once, *args, **kwargs)

    def assert_one_partial_match(self, *args, **kwargs):
        self.assert_quantified_partial_match(once, *args, **kwargs)

    def assert_all_partial_match(self, *args, **kwargs):
        self.assert_quantified_partial_match(always, *args, **kwargs)

    def assert_any_result_match(self, result_praedicate):
        self.assert_quantified_result_match(at_least_once, result_praedicate)

    def assert_one_result_match(self, result_praedicate):
        self.assert_quantified_result_match(once, result_praedicate)

    def assert_all_result_match(self, *args, **kwargs):
        self.assert_quantified_result_match(always, *args, **kwargs)

    def reset_invocations(self):
        self.successful_invocations = []
        return True

    def reset_results(self):
        self.successful_results = []
        return True


def _align_args_kwargs_to_argspec_args(argspec_args, args, kwargs):
    aligned_map = dict(zip(argspec_args[:len(args)], args))
    aligned_map.update((k, v) for k, v in kwargs.items() if k in argspec_args)
    return aligned_map


def _apply_praedicate_map_to_value_map(praedicate_map, value_map):
    for key in set(praedicate_map.keys()):
        yield praedicate_map[key](value_map[key])


def _apply_praedicate_list_to_value_list(praedicate_list, value_list):
    for praedicate, value in islice(zip(praedicate_list, value_list), 0, len(praedicate_list)):
        yield praedicate(value)


def _calculate_match(argspec, praedicate_args, praedicate_kwargs, call_args, call_kwargs, exact=True):
    if argspec.defaults:
        aligned_call_args = dict(zip(argspec.args[len(argspec.defaults)+1::-1], argspec.defaults[::-1]))
    else:
        aligned_call_args = {}
    aligned_call_args.update(_align_args_kwargs_to_argspec_args(argspec.args, call_args, call_kwargs))
    aligned_praedicate_args = _align_args_kwargs_to_argspec_args(argspec.args, praedicate_args, praedicate_kwargs)

    extra_call_args = call_args[len(argspec.args):]
    extra_praedicate_args = praedicate_args[len(argspec.args):]

    extra_call_kwargs = dict((k, v) for k, v in call_kwargs.items() if k not in aligned_call_args)
    extra_praedicate_kwargs = dict((k, v) for k, v in praedicate_kwargs.items() if k not in aligned_praedicate_args)

    if exact:
        matching_named_call_args = set(aligned_call_args.keys()) == set(aligned_praedicate_args.keys())
        matching_extra_args = len(extra_call_args) == len(extra_praedicate_args)
        matching_extra_kwargs = set(extra_call_kwargs.keys()) == set(extra_praedicate_kwargs.keys())
    else:
        matching_named_call_args = set(aligned_call_args.keys()) >= set(aligned_praedicate_args.keys())
        matching_extra_args = len(extra_call_args) >= len(extra_praedicate_args)
        matching_extra_kwargs = set(extra_call_kwargs.keys()) >= set(extra_praedicate_kwargs.keys())

    if matching_named_call_args and matching_extra_args and matching_extra_kwargs:
        all_named_pass = all(_apply_praedicate_map_to_value_map(aligned_praedicate_args, aligned_call_args))
        all_extra_args_pass = all(_apply_praedicate_list_to_value_list(extra_praedicate_args, extra_call_args))
        all_extra_kwargs_pass = all(_apply_praedicate_map_to_value_map(extra_praedicate_kwargs, extra_call_kwargs))
        return all_named_pass and all_extra_args_pass and all_extra_kwargs_pass
    else:
        return False


def times(num_times):
    """
    Create a praedicate that checks to see if the number of matching invocations occur exactly the specified number
    of times.
    :param num_times: The exact number of matches that must have occurred.
    :return: A praedicate to check the resulting matching invocations list.
    """
    def praedicate(matching_invocations, _):
        return len(matching_invocations) == num_times
    return praedicate

once = times(1)
never = times(0)


def at_least_times(num_times):
    """
    Create a praedicate that checks to see if the number of matching invocations occur at least the specified number
    of times.
    :param num_times: The minimum number of matches that must have occurred.
    :return: A praedicate to check the resulting matching invocations list.
    """
    def praedicate(matching_invocations, _):
        return len(matching_invocations) >= num_times
    return praedicate

at_least_once = at_least_times(1)


def always(matching_invocations, all_invocations):
    """
    This praedicate verifies that all invocations must have matched.
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
    This praedicate will always return True, and thus matches anything.
    :param _: The argument, which is ignored.
    :return: True
    """
    return True


def any_of(elements):
    """
    Check to see if the argument is contained in a list of possible elements.
    :param elements: The elements to check the argument against in the praedicate.
    :return: A praedicate to check if the argument is a constituent element.
    """
    def praedicate(argument):
        return argument in elements
    return praedicate


def equal_to(element):
    """
    Check to see if the argument is equal to the specified element
    :param element: The element to check against the argument.
    :return: A praedicate to check if the argument is equal to the element.
    """
    def praedicate(argument):
        return argument == element
    return praedicate


def identical_to(element):
    """
    Check to see if the argument is identical to the specified element
    :param element: The element to check against the argument.
    :return: A praedicate to check if the argument is identical to the element.
    """
    def praedicate(argument):
        return element is argument
    return praedicate


def instance_of(cls):
    """
    Check to see if the argument is an instance of the specified class element.
    :param cls: The element to use to check inheritance of the argument.
    :return: A praedicate to check if the argument an instance of the element.
    """
    def praedicate(argument):
        return isinstance(argument, cls)
    return praedicate
