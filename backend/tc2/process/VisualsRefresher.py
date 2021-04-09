import threading
import time as pytime
from datetime import datetime
from threading import Thread
from typing import List

from tc2.env.TimeEnv import TimeEnv
from tc2.log.LogFeed import LogFeed
from tc2.log.Loggable import Loggable


class VisualsRefresher(Loggable):
    """
    A manager in charge of automatically updating visuals in the background via API calls.
    Not to be confused with VisualsGenerator, which receives the API calls and actually updates the visuals.
    """
    live_time_env: TimeEnv
    symbols: List[str]
    visuals_updates_thread: Thread

    def __init__(self, logfeed_program: LogFeed, logfeed_process: LogFeed, symbols: List[str],
                 live_time_env: TimeEnv):
        super().__init__(logfeed_program=logfeed_program, logfeed_process=logfeed_process)

        self.live_time_env = live_time_env
        self.symbols = symbols

    def start(self) -> None:
        """
        Schedules visuals to update automatically.
        These scheduled updates are in addition to updates initiated by the user manually using the webpanel.
        """

        # Stop the already-running thread, if active
        self.stop()

        # Continuously initiate data updates for visuals, in a separate thread
        self.visuals_updates_thread = threading.Thread(target=self._updates_logic)
        self.visuals_updates_thread.start()

    def stop(self) -> None:
        """Stops the running thread, if active."""
        try:
            self.visuals_updates_thread.do_run = False
        except Exception:
            pass

    def _updates_logic(self) -> None:
        """
        Starts an infinite loop that updates visuals continuously.
        """
        self.info_process('Starting visual updates thread')
        visuals_updated = []
        while getattr(threading.current_thread(), "do_run", True):
            # Wait a long time between updates since they are run continuously
            pytime.sleep(5)

            # TODO Ensure we have a valid auth token for the API

            expected_update_time = self.live_time_env.now()

            # Price graph visual
            # Iterate thru each symbol before each visual (so that updates are evenly distributed)
            symbol_index = 0
            while symbol_index < len(self.symbols):
                symbol = self.symbols[symbol_index]

                if f'price-graph-{symbol}' not in visuals_updated:
                    # TODO Update price graph visual for symbol
                    while not self.is_updated('TODO', expected_update_time):
                        pytime.sleep(2)
                    visuals_updated.append(f'price-graph-{symbol}')
                    break
                symbol_index += 1

            if symbol_index < len(self.symbols) - 1:
                continue

            # Run history visual (paper account)
            if 'run-history-paper' not in visuals_updated:
                # TODO Update trade history visual for paper account
                while not self.is_updated('TODO', expected_update_time):
                    pytime.sleep(2)
                visuals_updated.append('run-history-paper')
                continue

            # Run history visual (live account)
            if 'run-history-live' not in visuals_updated:
                # TODO Update trade history visual for live account
                while not self.is_updated('TODO', expected_update_time):
                    pytime.sleep(2)
                visuals_updated.append('run-history-live')
                continue

            # TODO Automatically update other visuals

            # Allow visuals to update again once all have been processed
            visuals_updated = []

    def is_updated(self, api_call: str, expected_update_time: datetime) -> bool:
        """Gets the latest update time of the visual, returns True if it is recent."""
        # TODO Make the api call

        # TODO Convert last_updated to a datetime
        last_updated = self.live_time_env.now()

        # Return whether the visual was recently updated
        return last_updated >= expected_update_time
