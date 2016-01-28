from unittest import TestCase

from testtoolbox import BDD


class ExampleTest(TestCase):
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