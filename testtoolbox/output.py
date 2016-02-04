from __future__ import print_function
from collections import namedtuple
from functools import partial


class ANSITermCodes(object):
    WHITE = '\033[37m'
    CYAN = '\033[36m'
    PURPLE = '\033[35m'
    BLUE = '\033[34m'
    YELLOW = '\033[33m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    BLACK = '\033[30m'
    NORMAL_COLOR = '\033[39m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    HALF_BRIGHT = '\033[1m'
    NORMAL_BRIGHT = '\033[22m'
    UNDERLINE = '\033[4m'
    UNDERLINE_OFF = '\033[24m'
    BLINK = '\033[5m'
    BLINK_OFF = '\033[25m'


def _output_formatter(output_code, text, terminator_code=ANSITermCodes.RESET):
    return "%s%s%s" % (output_code, str(text), terminator_code)


purple = partial(_output_formatter, ANSITermCodes.PURPLE, terminator_code=ANSITermCodes.NORMAL_COLOR)
green = partial(_output_formatter, ANSITermCodes.GREEN, terminator_code=ANSITermCodes.NORMAL_COLOR)
red = partial(_output_formatter, ANSITermCodes.RED, terminator_code=ANSITermCodes.NORMAL_COLOR)
yellow = partial(_output_formatter, ANSITermCodes.YELLOW, terminator_code=ANSITermCodes.NORMAL_COLOR)
blue = partial(_output_formatter, ANSITermCodes.BLUE, terminator_code=ANSITermCodes.NORMAL_COLOR)
cyan = partial(_output_formatter, ANSITermCodes.CYAN, terminator_code=ANSITermCodes.NORMAL_COLOR)
black = partial(_output_formatter, ANSITermCodes.BLACK, terminator_code=ANSITermCodes.NORMAL_COLOR)
white = partial(_output_formatter, ANSITermCodes.WHITE, terminator_code=ANSITermCodes.NORMAL_COLOR)
bold = partial(_output_formatter, ANSITermCodes.BOLD, terminator_code=ANSITermCodes.NORMAL_BRIGHT)
half_bright = partial(_output_formatter, ANSITermCodes.HALF_BRIGHT, terminator_code=ANSITermCodes.NORMAL_BRIGHT)
underline = partial(_output_formatter, ANSITermCodes.UNDERLINE, terminator_code=ANSITermCodes.UNDERLINE_OFF)
blinking = partial(_output_formatter, ANSITermCodes.BLINK, terminator_code=ANSITermCodes.BLINK_OFF)


def _print_formatter(color_str, *args):
    args = args + (ANSITermCodes.RESET,)
    new_first_arg = "%s%s" % (color_str, args[0]) if args else color_str
    print(new_first_arg, *args[1:])


print_purple = partial(_print_formatter, ANSITermCodes.PURPLE)
print_green = partial(_print_formatter, ANSITermCodes.GREEN)
print_red = partial(_print_formatter, ANSITermCodes.RED)
print_yellow = partial(_print_formatter, ANSITermCodes.YELLOW)
print_cyan = partial(_print_formatter, ANSITermCodes.CYAN)
print_blue = partial(_print_formatter, ANSITermCodes.BLUE)
print_black = partial(_print_formatter, ANSITermCodes.BLACK)
print_white = partial(_print_formatter, ANSITermCodes.WHITE)
print_bold = partial(_print_formatter, ANSITermCodes.BOLD)
print_half_bright = partial(_print_formatter, ANSITermCodes.HALF_BRIGHT)
print_underline = partial(_print_formatter, ANSITermCodes.UNDERLINE)
print_blinking = partial(_print_formatter, ANSITermCodes.BLINK)
TestOutputFunctions = namedtuple("TestOutputFunctions", ["info", "pass_", "ignore", "warn", "fail"])
DefaultOutputFunctions = TestOutputFunctions(print_purple, print_green, print_green, print_yellow, print_red)