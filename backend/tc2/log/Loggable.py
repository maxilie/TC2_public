from typing import Optional

from tc2.log.LogFeed import LogFeed, LogLevel


class Loggable:
    """
    Allows any class to send logs to the program logfeed and another, optional logfeed.
    For example, trading tasks need to extend Loggable so they can log details on the 'trading' logfeed and warnings
    on the program logfeed.
    """
    logfeed_program: Optional[LogFeed]
    logfeed_process: Optional[LogFeed]

    def __init__(self, logfeed_program: Optional[LogFeed], logfeed_process: Optional[LogFeed] = None) -> None:
        """
        :param logfeed_program: can be set to None to disable all logging
        :param logfeed_process: can be set to None to disable minor logging
        """
        self.logfeed_program = logfeed_program
        self.logfeed_process = logfeed_process

    def info_main(self, msg: str) -> None:
        """Logs an info message to the program logfeed."""
        if self.logfeed_program is not None:
            self.logfeed_program.log(LogLevel.INFO, msg)

    def warn_main(self, msg: str) -> None:
        """Logs a warning message to the program logfeed."""
        if self.logfeed_program is not None:
            self.logfeed_program.log(LogLevel.WARNING, msg)

    def error_main(self, msg: str) -> None:
        """Logs an error message to the program logfeed."""
        if self.logfeed_program is not None:
            self.logfeed_program.log(LogLevel.ERROR, msg)

    def debug_process(self, msg: str) -> None:
        """Logs a debug message to the process logfeed."""
        if self.logfeed_process is not None:
            self.logfeed_process.log(LogLevel.DEBUG, msg)

    def info_process(self, msg: str) -> None:
        """Logs an info message to the process logfeed."""
        if self.logfeed_process is not None:
            self.logfeed_process.log(LogLevel.INFO, msg)

    def warn_process(self, msg: str) -> None:
        """Logs a warning message to the process logfeed."""
        if self.logfeed_process is not None:
            self.logfeed_process.log(LogLevel.WARNING, msg)

    def error_process(self, msg: str) -> None:
        """Logs an error message to the process logfeed."""
        if self.logfeed_process is not None:
            self.logfeed_process.log(LogLevel.ERROR, msg)
