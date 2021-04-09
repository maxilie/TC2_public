import multiprocessing
import os
import time as pytime
from datetime import date, datetime
from enum import Enum
from multiprocessing import Queue
from threading import Lock, Thread
from typing import TextIO

from tc2.util.date_util import DATE_FORMAT

MAX_LINES_PER_FILE = 1000

MAX_LINES_PER_SECOND = 200

LOGFILE_TIME_FORMAT = '%-I:%M%p.%S%f'


class LogCategory(Enum):
    # LogFeed for messages pertaining to program startup/shutdown tasks
    # and important messages from other feeds
    PROGRAM = 'program'

    # LogFeed for messages pertaining to live data collection, re-collection,
    # and training of analysis models
    DATA = 'data'

    # LogFeed for messages pertaining to live strategy execution
    LIVE_TRADING = 'live_trading'

    # LogFeed for messages pertaining to optimization of a strategy's
    # model weights via evaluation of simulated strategy runs
    OPTIMIZATION = 'optimization'

    # LogFeed for messages pertaining to the handling of API calls
    API = 'api'

    # LogFeed for messages pertaining to the generation of visuals
    VISUALS = 'visuals'


class LogLevel(Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


class LogFeed:
    """A stream-like manager that handles logs for a specific process (LogCategory)."""

    process: LogCategory
    logDir: str
    lock: Lock
    queue: Queue
    _last_date: 'multiprocessing list'

    def __init__(self, system: LogCategory) -> None:
        self.process = system
        self.logDir = f'logs/{system.value}'
        self.lock = Lock()
        self.queue = Queue(maxsize=MAX_LINES_PER_SECOND)
        self._last_date = multiprocessing.Manager().list()
        self._last_date.append(datetime.now().strftime(DATE_FORMAT))

        # Create a folder for the logfiles
        if not os.path.exists(self.logDir):
            os.mkdir(self.logDir)

        # Start a task to print queued log messages every second
        def print_from_queue():
            while True:
                pytime.sleep(1)
                if self.queue.empty():
                    continue
                with self.lock:
                    logfile = self.get_latest_logfile()
                    logfile.seek(0, os.SEEK_END)
                    while not self.queue.empty():
                        msg = self.queue.get()
                        # Add the log event to the latest logfile
                        logfile.write(msg + "\n")
                    logfile.close()

        thread = Thread(target=print_from_queue)
        thread.start()

    def log(self, level: LogLevel, msg: str):
        # Prepend a prefix showing the log's event level its time
        prefix = '[' + level.value + ' ' + datetime.now().strftime(LOGFILE_TIME_FORMAT)[0:-4] + ']'
        msg = prefix + " " + msg

        # Log each new date
        if self._last_date[0] != datetime.now().strftime(DATE_FORMAT):
            self._last_date[0] = datetime.now().strftime(DATE_FORMAT)
            new_date_msg = '      ' + datetime.now().strftime('%A, %b %d')
            print(new_date_msg, flush=True)
            try:
                self.queue.put_nowait(new_date_msg)
            except Exception as e:
                pass

        # Print program logs to console, flushing the stream to print instantly from any thread/process
        if self.process is LogCategory.PROGRAM:
            print(msg, flush=True)

        try:
            self.queue.put(msg, timeout=2)
        except Exception as e:
            print(f'{prefix} {self.process.value} logfeed queue overwhelmed')

    def get_latest_logfile(self) -> TextIO:
        # Ensure the logfile directory exists
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir, exist_ok=True)

        # Find a logfile that hasn't been filled yet
        files_filled = 0
        filename = self.get_logfile_name(date.today(), files_filled)
        file = open(filename, 'a+')
        file.seek(0)
        while os.path.exists(filename) and os.path.isfile(filename) and self.get_num_lines(file) >= MAX_LINES_PER_FILE:
            file.close()
            files_filled = files_filled + 1
            filename = self.get_logfile_name(date.today(), files_filled)
            file = open(filename, 'a+')
            file.seek(0)
        file.close()

        # Open the logfile in 'append' mode so changes can be made
        logfile = open(filename, 'a+')

        # Seek to the top of the logfile so all its contents can be read
        logfile.seek(0)
        return logfile

    def get_logfile_name(self, log_date: date, log_number: int) -> str:
        return self.logDir + '/' + log_date.__str__() + "_" + str(log_number) + ".txt"

    @staticmethod
    def get_num_lines(log_file) -> int:
        return len(log_file.readlines())
