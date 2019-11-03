from unittest import TestCase

# Fix some bad assertpy import behavior in Python 3.4 by preimporting collections.abc
try:
    import collections.abc
except ImportError:
    pass

from assertpy import assert_that

from test_toolbox.bdd import BDD
from test_toolbox.output import DefaultOutputFunctions, TestOutputFunctions
from test_toolbox.spy import apply_function_spy, contains


class BDDModuleUnitTests(TestCase):
    @staticmethod
    def generate_spied_output_functions():
        return TestOutputFunctions(*map(apply_function_spy, DefaultOutputFunctions))

    def test_bdd_controller_pass(self):
        output_functions = self.generate_spied_output_functions()
        with BDD.scenario("I am testing some random stuff in Python", output_functions=output_functions) as bdd:
            bdd.given("I set up three integer variables")

            x = 1
            y = 2
            z = 3

            bdd.then("These integers should be associative and commutative")
            assert_that(x + y).is_equal_to(y + x)
            assert_that((x + y) + z).is_equal_to(x + (y + z))
        output_functions.info.assert_any_partial_match(
            contains("I am testing some random stuff in Python"))
        output_functions.pass_.assert_any_partial_match(
            contains("I set up three integer variables"))
        output_functions.pass_.assert_any_partial_match(
            contains("These integers should be associative and commutative"))
        assert_that(output_functions.fail.num_invocations).is_zero()
        assert_that(output_functions.warn.num_invocations).is_zero()

    def test_bdd_controller_fail(self):
        output_functions = self.generate_spied_output_functions()

        def do_test():
            with BDD.scenario("I am trying to cause something to fail", output_functions=output_functions) as bdd:
                bdd.given("I set up some random garbage")

                a = 1
                b = 2

                with bdd.and_("I drop into a setup with other clauses") as clause:
                    clause.then("I add two variables")
                    a + b

                bdd.then("I throw an assertion")
                assert False, "I don't know why"

        self.assertRaises(AssertionError, do_test)
        output_functions.info.assert_any_partial_match(
            contains("I am trying to cause something to fail"))

        output_functions.pass_.assert_any_partial_match(
            contains("I set up some random garbage"))
        output_functions.pass_.assert_any_partial_match(
            contains("I drop into a setup with other clauses"))
        output_functions.pass_.assert_any_partial_match(
            contains("I add two variables"))

        output_functions.fail.assert_any_partial_match(
            contains("I throw an assertion"))
        output_functions.fail.assert_any_partial_match(
            contains("AssertionError"))
        output_functions.fail.assert_any_partial_match(
            contains("I don't know why"))
        assert_that(output_functions.warn.num_invocations).is_zero()
