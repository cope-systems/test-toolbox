# Python Test Toolbox
### A simple set of enhancements and tools for unittest compatible tests.

This library adds a number of extras for unittest-based test code to enhance
understandability, and reduce duplicate code.

### Features
#### Output formatting code

Most of the commonly available ANSI formatters (which provide nice colored output on terminals, 
or properties like bolding), are conveniently wrapped in the output module of testtoolbox.

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
    >>> from testtoolbox.output import print_purple, purple, bold
    >>> print_purple("Just", "like", "regular", "print,", "except purple")
    Just like regular print, except purple
    >>> bold_purple_str = bold(purple("this is a string"))
```

#### Test Flow Modifiers

These provide captioning and explanation for both the BDD style, and for basic unit test style.

BDD Example:

```
    from testtoolbox.testflow import BDD
    
    bdd = BDD()
    
    with bdd.given("the integer 1"):
         a = 1
         
    with bdd.when("it is multiplied by two"):
         a *= 2
         
    with bdd.then("it should be equal to two"):
         assert a == 2
```

This can be used in conjunction with the unittest decorators, and can be nested:

```
    from unittest import TestCase
    
    from testtoolbox.testflow import should, scenario_descriptor, feature, BDD
    from testtoolbox.helpers import modify_buffer_object
    
    
    @feature("The testtoolbox code and some other Python")
    class ExampleTest(TestCase):
        """
        Lorem Ipsum blah blah blah
        """
    
        @scenario_descriptor("The number one", should("be the identity element for multiplication on real numbers"))
        def test_simple_bdd_tool(self):
            bdd = BDD()
            
            with bdd.given("the integer 1"):
                a = 1
         
            with bdd.when("it is multiplied by two"):
                a *= 2
         
            with bdd.then("it should be equal to two"):
                assert a == 2
```

#### Helper functions

Also included are some generic functions that are often replicated or missing (but needed) when testing.
These include:

  * await_condition: Wait for a specified callable to return true within a given time, or assert on timeout.
  
  * modify_buffer_object: Modify a python object that supports the buffer interface in place (good for mocking socket.recv_into)

# Other recommended libraries

An excellent supplement to this library is the assertpy library, which provides an excellent set of literate asserts.
See: https://github.com/ActivisionGameScience/assertpy