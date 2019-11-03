# Python Test Toolbox
[![Build Status](https://travis-ci.org/cope-systems/test-toolbox.svg?branch=master)](https://travis-ci.org/cope-systems/test-toolbox)
[![Documentation Status](https://readthedocs.org/projects/test-toolbox/badge/?version=latest)](https://test-toolbox.readthedocs.io/en/latest/?badge=latest)

The full documentation is availalbe [here.](https://test-toolbox.readthedocs.io/en/latest/)

### A simple set of enhancements and tools for unittest compatible tests.

This library adds a number of extras for test code written in Python in order to enhance understandability, 
and reduce duplicate code.

### Features
#### Output formatting code

Most of the commonly available ANSI formatters (which provide nice colored output on terminals, 
or properties like bolding), are conveniently wrapped in the output module of test_toolbox.

Supported ANSI modes:

  * White Text
  * Cyan Text
  * Purple Text
  * Yellow Text
  * Green Text
  * Red Text
  * Black Text
  * Bold Text
  * Half Bright Text
  * Underlined Text
  * Blinking Text (on supported terminals)
  
These are accessible both through convenience print functions, as well as raw text format functions. For example:

```
    >>> from test_toolbox.output import print_purple, purple, bold
    >>> print_purple("Just", "like", "regular", "print,", "except purple")
    Just like regular print, except purple
    >>> bold_purple_str = bold(purple("this is a string"))
```

#### Test Flow Modifiers

These provide captioning and explanation for both the BDD style, and for basic unit test style.

BDD Example:

```
    from test_toolbox.testflow import BDD
    
    with BDD.scenario("Testing on integers") as bdd:
    
        bdd.given("the integer 1")
        a = 1
         
        bdd.when("it is multiplied by two")
        a *= 2
         
        bdd.then("it should be equal to two")
        assert a == 2
```

This can be used in conjunction with the unittest decorators, and can be nested:

```
    from unittest import TestCase
    
    from test_toolbox.testflow import should, scenario_descriptor, feature, BDD
    from test_toolbox.helpers import modify_buffer_object
    
    
    @feature("The test_toolbox code and some other Python")
    class ExampleTest(TestCase):
        """
        Lorem Ipsum blah blah blah
        """
    
        @scenario_descriptor("The number one", should("be the identity element for multiplication on real numbers"))
        def test_simple_bdd_tool(self):
            with BDD() as bdd:
                bdd.given("the integer 1")
                a = 1
         
                bdd.when("it is multiplied by two")
                a *= 2
         
                bdd.then("it should be equal to two")
                assert a == 2
```

#### Helper functions

Also included are some generic functions that are often replicated or missing (but needed) when testing.
These include:

  * await_condition: Wait for a specified callable to return true within a given time, or assert on timeout.
  
  * modify_buffer_object: Modify a python object that supports the buffer interface in place (good for mocking socket.recv_into)
  
#### Spies for Python callables

Another useful and powerful tool included in this toolbox is the callable Spy implementation. This tool allows testers
to monitor and reason about invoked callables that can be dependency injected or monkey patched in test code. The Spy
can be both applied to mock instances of an object, as well as applied in-situ to real objects. The Spy also has a 
powerful matching system that aligns specified praedicates to callable invocations to get fine grained (and user-extendable)
checking of how a callable is being used.

Example:

```
     from test_toolbox.spy import apply_function_spy, equal_to, any_of, instance_of
    
     @apply_function_spy
     def my_function(foo, bar=2):
         return foo + bar
         
     my_function(1)
     my_function.assert_one_exact_match(instance_of(int), equal_to(2))
     
     my_function(5)
     
     # Use a user created praedicate
     def is_positive(argument):
          return argument > 0
          
     my_function.assert_all_partial_match(is_positive)
    
```

# Other recommended libraries

An excellent supplement to this library is the assertpy library, which provides an excellent set of literate asserts.
See: https://github.com/ActivisionGameScience/assertpy
