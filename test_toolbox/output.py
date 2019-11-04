"""
The output module provides convenience methods for utilizing ANSI terminal color codes,
which may be used to help visually differentiate output from scripts and tests.

There are two ways primary ways to consume this module: using output formatter functions or using
print wrapper functions.

The following output format functions may be used to generate new text with the appropriate ANSI terminal
codes to get the named effect:

* purple()
* green()
* red()
* yellow()
* green()
* blue()
* cyan()
* white()
* bold()
* half_bright()
* underline()
* blinking()

Each of these functions takes one argument and returns a string.

The following print functions work as you would expect the normal print function to, but print the
arguments to the function with the named effect:

* print_purple()
* print_green()
* print_red()
* print_yellow()
* print_cyan()
* print_blue()
* print_black()
* print_white()
* print_bold()
* print_half_bright()
* print_underline()
* print_blinking()

All of these functions have the same arity as the underlying print function (that is to say they all may
take zero or more arguments).
"""
from __future__ import print_function

import textwrap
from collections import namedtuple
from functools import partial
import sys

IS_PY2 = sys.version_info[0] == 2


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
    return "{0}{1}{2}".format(output_code, text, terminator_code)


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
    if args:
        args = ("{0}{1}".format(color_str, args[0]),) + args[1:]
    else:
        args = (color_str,)
    args = args + (ANSITermCodes.RESET,)
    if IS_PY2:
        print(*map(unicode, args))
    else:
        print(*args)


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


def wrap_text_cleanly(text, width=120, preserve_newlines=False, initial_indent='', subsequent_indent='\t\t'):
    text_units = text.split('\n') if preserve_newlines else [text]
    wrap_function = partial(textwrap.wrap, width=width, initial_indent=initial_indent,
                            subsequent_indent=subsequent_indent)
    cleaned_text_units = map(wrap_function, text_units)
    return "\n".join([line for text_unit in cleaned_text_units for line in text_unit])
