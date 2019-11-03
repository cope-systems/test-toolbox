from unittest import TestCase
import time


from test_toolbox.helpers import await_condition


class HelpersModuleUnitTests(TestCase):
    def test_await_condition(self):
        current_time = time.time()

        await_condition("Should never fail!", lambda: True)
        await_condition("Should never fail!", lambda: time.time() > (current_time + 0.3))

        self.assertRaises(
            AssertionError,
            await_condition,
            "Should always fail",
            lambda: False,
            timeout=0.5
        )
