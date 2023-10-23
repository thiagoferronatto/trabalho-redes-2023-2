"""
style.py

Authors: Thiago Ferronatto and Yuri Moraes Gavilan

This file contains a class used as an abstraction for command-line text styling.
"""


class Style:
    """
    A class that provides static methods and constants for applying colors and
    formatting to text objects. The class uses ANSI escape codes to modify the
    text appearance in the terminal. The class has constants for different
    colors and styles, such as PINK, BLUE, CYAN, GREEN, RED, WARNING, FAIL,
    ENDC, BOLD, and UNDERLINE. The class also has methods for each color and
    style that take an object as an argument and return a formatted string with
    the corresponding escape codes. For example, Style.blue("Hello") returns
    "\033[94mHello\033[0m", which prints "Hello" in blue color in the terminal.
    """

    PINK = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    def blue(obj):
        return f"{Style.BLUE}{obj}{Style.ENDC}"

    def green(obj):
        return f"{Style.GREEN}{obj}{Style.ENDC}"

    def red(obj):
        return f"{Style.RED}{obj}{Style.ENDC}"

    def bold(obj):
        return f"{Style.BOLD}{obj}{Style.ENDC}"

    def warn(obj):
        return f"{Style.WARNING}{obj}{Style.ENDC}"

    def fail(obj):
        return f"{Style.FAIL}{obj}{Style.ENDC}"

    def pink(obj):
        return f"{Style.PINK}{obj}{Style.ENDC}"
