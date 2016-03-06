import inspect
from functools import update_wrapper
from types import MethodType, FunctionType, BuiltinFunctionType
from collections import namedtuple

CallableInvocation = namedtuple("CallableInvocation", ("args", "kwargs"))


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
        self.verbose = verbose

    def __call__(self, *args, **kwargs):
        result = self.target_func(*args, **kwargs)
        if self.is_method:
            self.successful_invocations.append(CallableInvocation(args[1:], kwargs))
        else:
            self.successful_invocations.append(CallableInvocation(args, kwargs))
        return result

    def __get__(self, instance, owner):
        return self.get_type(self, instance, owner)

    @property
    def num_invocations(self):
        return len(self.successful_invocations)

    def check_quantified_exact_match(self, times_praedicate, *args, **kwargs):
        def check_invocation(invocation_data):
            return calculate_exact_match(self.target_func_argspec, args, kwargs, *invocation_data)
        return times_praedicate(
            filter(None, map(check_invocation, self.successful_invocations)),
            self.successful_invocations
        )

    def check_quantified_partial_match(self, times_praedicate, *args, **kwargs):
        def check_invocation(invocation_data):
            return calculate_partial_match(self.target_func_argspec, args, kwargs, *invocation_data)
        return times_praedicate(
            filter(None, map(check_invocation, self.successful_invocations)),
            self.successful_invocations
        )

    def assert_quantified_exact_match(self, times_praedicate, *args, **kwargs):
        result = self.check_quantified_exact_match(times_praedicate, *args, **kwargs)
        if not result and not self.verbose:
            raise AssertionError("Failed to find a matching exact invocation!")
        elif not result:
            raise AssertionError(
                "Failed to find a matching partial invocation!\n"
                "All invocations:\n[{}]".format(",\n".join(map(repr, self.successful_invocations)))
            )

    def assert_quantified_partial_match(self, times_praedicate, *args, **kwargs):
        result = self.check_quantified_partial_match(times_praedicate, *args, **kwargs)
        if not result and not self.verbose:
            raise AssertionError("Failed to find a matching partial invocation!")
        elif not result:
            raise AssertionError(
                "Failed to find a matching partial invocation!\n"
                "All invocations:\n[{}]".format(",\n".join(map(repr, self.successful_invocations)))
            )

    def assert_any_exact_match(self, *args, **kwargs):
        self.assert_quantified_exact_match(at_least_once, *args, **kwargs)

    def assert_one_exact_match(self, *args, **kwargs):
        self.assert_quantified_exact_match(once, *args, **kwargs)

    def assert_any_partial_match(self, *args, **kwargs):
        self.assert_quantified_partial_match(at_least_once, *args, **kwargs)

    def assert_one_partial_match(self, *args, **kwargs):
        self.assert_quantified_partial_match(once, *args, **kwargs)

    def clear_invocations(self):
        self.successful_invocations = []
        return True


def calculate_exact_match(argspec, praedicate_args, praedicate_kwargs, call_args, call_kwargs):
    if argspec.defaults:
        aligned_call_args = dict(zip(argspec.args[len(argspec.defaults)+1::-1], argspec.defaults[::-1]))
    else:
        aligned_call_args = {}
    aligned_call_args.update(zip(argspec.args[:len(call_args)], call_args))
    aligned_call_args.update((k, v) for k, v in call_kwargs.items() if k in argspec.args)
    aligned_praedicate_args = dict(zip(argspec.args[:len(praedicate_args)], praedicate_args))
    aligned_praedicate_args.update((k, v) for k, v in praedicate_kwargs.items() if k in argspec.args)

    extra_call_args = call_args[len(argspec.args):]
    extra_praedicate_args = praedicate_args[len(argspec.args):]

    extra_call_kwargs = dict((k, v) for k, v in call_kwargs.items() if k not in aligned_call_args)
    extra_praedicate_kwargs = dict((k, v) for k, v in praedicate_kwargs.items() if k not in aligned_praedicate_args)

    matching_named_call_args = set(aligned_call_args.keys()) == set(aligned_praedicate_args.keys())
    matching_extra_args = len(extra_call_args) == len(extra_praedicate_args)
    matching_extra_kwargs = set(extra_call_kwargs.keys()) == set(extra_praedicate_kwargs.keys())

    if matching_named_call_args and matching_extra_args and matching_extra_kwargs:
        all_named_pass = all(aligned_praedicate_args[key](aligned_call_args[key]) for key in aligned_call_args.keys())
        all_extra_args_pass = all(map(lambda d: d[0](d[1]), zip(extra_praedicate_args, extra_call_args)))
        all_extra_kwargs_pass = all(extra_praedicate_kwargs[key](extra_call_kwargs[key]) for key in extra_call_kwargs.keys())
        return all_named_pass and all_extra_args_pass and all_extra_kwargs_pass
    else:
        return False


def calculate_partial_match(argspec, praedicate_args, praedicate_kwargs, call_args, call_kwargs):
    if argspec.defaults:
        aligned_call_args = dict(zip(argspec.args[len(argspec.defaults)+1::-1], argspec.defaults[::-1]))
    else:
        aligned_call_args = {}
    aligned_call_args.update(zip(argspec.args[:len(call_args)], call_args))
    aligned_call_args.update((k, v) for k, v in call_kwargs.items() if k in argspec.args)
    aligned_praedicate_args = dict(zip(argspec.args[:len(praedicate_args)], praedicate_args))
    aligned_praedicate_args.update((k, v) for k, v in praedicate_kwargs.items() if k in argspec.args)

    extra_call_args = call_args[len(argspec.args):]
    extra_praedicate_args = praedicate_args[len(argspec.args):]

    extra_call_kwargs = dict((k, v) for k, v in call_kwargs.items() if k not in aligned_call_args)
    extra_praedicate_kwargs = dict((k, v) for k, v in praedicate_kwargs.items() if k not in aligned_praedicate_args)

    matching_named_call_args = set(aligned_call_args.keys()) >= set(aligned_praedicate_args.keys())
    matching_extra_args = len(extra_call_args) >= len(extra_praedicate_args)
    match_extra_kwargs = set(extra_call_kwargs.keys()) >= set(extra_praedicate_kwargs.keys())

    if matching_named_call_args and matching_extra_args and match_extra_kwargs:
        all_named_pass = all(aligned_praedicate_args[key](aligned_call_args[key]) for key in aligned_praedicate_args.keys())
        all_extra_args_pass = all(map(lambda d: d[0](d[1]), zip(extra_praedicate_args, extra_call_args[:len(extra_praedicate_args)])))
        all_extra_kwargs_pass = all(extra_praedicate_kwargs[key](extra_call_kwargs[key]) for key in extra_praedicate_kwargs.keys())
        return all_named_pass and all_extra_args_pass and all_extra_kwargs_pass
    else:
        return False


def times(num_times):
    def praedicate(matching_invocations, _):
        return len(matching_invocations) == num_times
    return praedicate

once = times(1)
never = times(0)


def at_least_times(num_times):
    def praedicate(matching_invocations, _):
        return len(matching_invocations) >= num_times
    return praedicate

at_least_once = at_least_times(1)


def always(matching_invocations, all_invocations):
    return len(matching_invocations) == len(all_invocations)


def apply_builtin_function_spy(func):
    return Spy(func, is_not_inspectable=True)


def apply_function_spy(func):
    return Spy(func)


def apply_method_spy(func):
    return Spy(func, is_method=True)


def anything(_):
    return True


def any_of(elements):
    def praedicate(argument):
        return argument in elements
    return praedicate


def equal_to(element):
    def praedicate(argument):
        return argument == element
    return praedicate


def identical_to(element):
    def praedicate(argument):
        return element is argument
    return praedicate


def instance_of(cls):
    def praedicate(argument):
        return isinstance(argument, cls)
    return praedicate


def foo(func):
    def wat(*args, **kwargs):
        print args, kwargs
        return func(*args, **kwargs)
    return wat

if __name__ == "__main__":
    class Test(object):
        def __init__(self):
            pass

        @apply_method_spy
        def wat(self, wat):
            return wat

        def test(self):
            return True

    def hello(world):
        return False
    spied_hello = apply_function_spy(hello)
    spied_hello(1)
    spied_hello.assert_quantified_exact_match(times(1), anything)
    spied_hello.assert_quantified_exact_match(times(1), world=equal_to(1))
    spied_hello.assert_quantified_exact_match(never, equal_to(2))
    t = Test()
    t.wat(1)
    t.wat.assert_one_exact_match(anything)
    spied_len = apply_builtin_function_spy(len)
    assert spied_len([1]) == 1
    spied_len.assert_any_exact_match(equal_to([1]))
