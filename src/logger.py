"""
A logger to print troubleshooting information to a file
"""


from style import *
from datetime import *
from os import path, makedirs


class Logger:
    """
    A class to create and manage a logger object that prints and writes
    log messages with different levels to a given file.
    """

    INFO = 0
    WARNING = 1
    FAIL = 2
    INPUT = 3
    NONE = 4

    DIR = "../log"

    def __init__(__self__, log_file):
        """
        Initializes a logger object with a given log file.

        Parameters
        ----------
        log_file : str
            The name of the file to write the log messages.
        """
        if not path.exists(Logger.DIR):
            makedirs(Logger.DIR)
        __self__.file = open(f"{Logger.DIR}/{log_file}", "a", encoding="utf-8")

    def __del__(__self__):
        """
        Closes the log file when the logger object is deleted.
        """
        __self__.file.close()

    def log(__self__, message, level=NONE):
        """
        Prints and writes a log message with a given level.

        Parameters
        ----------
        message : str
            The content of the log message.

        level : int, optional
            The level of the log message, one of Logger.INFO, Logger.WARNING,
            Logger.FAIL, Logger.INPUT, or Logger.NONE. The default is
            Logger.NONE.
        """
        prefix = ""
        timestamp = str(datetime.now())
        if level == Logger.INFO:
            prefix = "[INFO]"
            print(f"{Style.blue(prefix)} {Style.green(timestamp)} {message}")
        elif level == Logger.WARNING:
            prefix = "[AVISO]"
            print(f"{Style.warn(prefix)} {Style.green(timestamp)} {message}")
        elif level == Logger.FAIL:
            prefix = "[ERRO]"
            print(f"{Style.fail(prefix)} {Style.green(timestamp)} {message}")
        elif level == Logger.INPUT:
            prefix = "[ENTRADA]"
            print(f"{Style.pink(prefix)} {Style.green(timestamp)} {message}")
        else:
            print(message)
        message = prefix + " " + timestamp + " " + message + "\n"
        __self__.file.write(message)
        __self__.file.flush()
