from __future__ import print_function

from unittest import TestCase

# Fix some bad assertpy import behavior in Python 3.4 by preimporting collections.abc
try:
    import collections.abc
except ImportError:
    pass

from assertpy import assert_that

import sys
import io


from test_toolbox.output import (
    ANSITermCodes, purple, green, red, yellow, blue, cyan, black, white,
    bold, half_bright, underline, blinking, print_purple, print_green, print_red,
    print_yellow, print_cyan, print_blue, print_black, print_white, print_bold,
    print_half_bright, print_underline, print_blinking
)


class OutputModuleUnitTests(TestCase):
    
    TEST_STRING = u"foobar"
    
    def test_output_functions(self):
        def assert_color_str(color_output_func, expected_color):
            assert_that(color_output_func(self.TEST_STRING)).contains(
                self.TEST_STRING, expected_color, ANSITermCodes.NORMAL_COLOR
            )
            
        def assert_effect_str(effect_func, expected_ansi_code, expected_terminator):
            assert_that(effect_func(self.TEST_STRING)).contains(
                self.TEST_STRING, expected_ansi_code, expected_terminator
            )

        assert_color_str(purple, ANSITermCodes.PURPLE)
        assert_color_str(green, ANSITermCodes.GREEN)
        assert_color_str(red, ANSITermCodes.RED)
        assert_color_str(yellow, ANSITermCodes.YELLOW)
        assert_color_str(blue, ANSITermCodes.BLUE)
        assert_color_str(cyan, ANSITermCodes.CYAN)
        assert_color_str(black, ANSITermCodes.BLACK)
        assert_color_str(white, ANSITermCodes.WHITE)

        assert_color_str(lambda s: bold(white(s)), ANSITermCodes.WHITE)
        assert_color_str(lambda s: half_bright(red(s)), ANSITermCodes.RED)
        assert_color_str(lambda s: yellow(blinking(s)), ANSITermCodes.YELLOW)
        assert_color_str(lambda s: purple(underline(s)), ANSITermCodes.PURPLE)

        assert_effect_str(bold, ANSITermCodes.BOLD, ANSITermCodes.NORMAL_BRIGHT)
        assert_effect_str(half_bright, ANSITermCodes.HALF_BRIGHT, ANSITermCodes.NORMAL_BRIGHT)
        assert_effect_str(underline, ANSITermCodes.UNDERLINE, ANSITermCodes.UNDERLINE_OFF)
        assert_effect_str(blinking, ANSITermCodes.BLINK, ANSITermCodes.BLINK_OFF)

    def test_print_function(self):

        fake_stdout = io.StringIO()
        old_stdout = sys.stdout
        
        def assert_effect(print_func, expected_ansi_code):
            print_func(self.TEST_STRING)
            assert_that(fake_stdout.getvalue()).contains(
                self.TEST_STRING, expected_ansi_code, ANSITermCodes.RESET
            )

        try:
            sys.stdout = fake_stdout

            print(u"Wat")
            assert_that(fake_stdout.getvalue()).contains(u"Wat")

            assert_effect(print_purple, ANSITermCodes.PURPLE)
            assert_effect(print_green, ANSITermCodes.GREEN)
            assert_effect(print_red, ANSITermCodes.RED)
            assert_effect(print_yellow, ANSITermCodes.YELLOW)
            assert_effect(print_blue, ANSITermCodes.BLUE)
            assert_effect(print_cyan, ANSITermCodes.CYAN)
            assert_effect(print_black, ANSITermCodes.BLACK)
            assert_effect(print_white, ANSITermCodes.WHITE)
            assert_effect(print_bold, ANSITermCodes.BOLD)
            assert_effect(print_half_bright, ANSITermCodes.HALF_BRIGHT)
            assert_effect(print_underline, ANSITermCodes.UNDERLINE)
            assert_effect(print_blinking, ANSITermCodes.BLINK)
        finally:
            sys.stdout = old_stdout
