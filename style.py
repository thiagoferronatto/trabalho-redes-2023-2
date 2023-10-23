# Colors and stuff to print things in the terminal


class Style:
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
