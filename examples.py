from unittest import TestCase

from testtoolbox import BDD, feature, scenario_descriptor, should, modify_buffer_object


@feature("The testtoolbox code and some other Python")
class ExampleTest(TestCase):
    """
    Lorem Ipsum blah blah blah
    """

    @scenario_descriptor("The BDD tool", should("look nice and produce reasonable output."))
    def test_simple_bdd_tool(self):
        bdd = BDD()

        with bdd.given("a positive number"):
            a = 9000

            with bdd.when("the number is multiplied by -1 "):
                a *= -1

            with bdd.then("the number should an int."):
                assert isinstance(a, int)

            with bdd.and_("the number show assert if we check if it's negative", ignore_exceptions=[AssertionError]):
                assert a > 0

            with bdd.and_("we should check to see if we're actually a float", warn_exceptions=[AssertionError]):
                assert isinstance(a, float)

            with bdd.also("we should do random things sometimes with impure I/O."):
                raise IOError("omgwtfbbq")

    @scenario_descriptor("The bytearray buffer", should("be modifiable inline."))
    def test_bytearray_modificiation(self):
        bdd = BDD()

        with bdd.given("a python bytearray object 20 bytes long"):
            some_bytearray = bytearray(20)

            with bdd.when("we use the modification function to modify it inline"):
                modify_buffer_object(b"hello world", some_bytearray)

            with bdd.then("the bytearray should be modified to contain the new value specified"):
                assert b"hello world" in some_bytearray
                assert len(some_bytearray) == 20