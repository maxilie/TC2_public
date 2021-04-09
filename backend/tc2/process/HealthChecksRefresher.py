import threading
import time as pytime
from datetime import time
from threading import Thread
from typing import List

from tc2.env.TimeEnv import TimeEnv
from tc2.log.LogFeed import LogFeed
from tc2.log.Loggable import Loggable
from tc2.util.TimeInterval import TimeInterval


class HealthChecksRefresher(Loggable):
    """
    A manager in charge of automatically performing health checks in the background via API calls.
    Not to be confused with HealthChecker, which receives the API calls and actually performs the health checks.
    """
    live_time_env: TimeEnv
    symbols: List[str]
    health_updates_thread: Thread

    def __init__(self, logfeed_program: LogFeed, logfeed_process: LogFeed, symbols: List[str],
                 live_time_env: TimeEnv):
        super().__init__(logfeed_program=logfeed_program, logfeed_process=logfeed_process)

        self.live_time_env = live_time_env
        self.symbols = symbols

    def start(self) -> None:
        """
        Schedules health checks to run automatically at night.
        These scheduled runs are in addition to runs initiated by the user manually using the webpanel.
        """

        # Stop the already-running thread, if active
        self.stop()

        # Create a time interval representing [6PM, 6AM]
        update_time_period = TimeInterval(self.logfeed_process, time(hour=18), time(hour=6))

        # Run health checks during the time interval, in a separate thread
        self.health_updates_thread = threading.Thread(target=self._updates_logic, args=[update_time_period])
        self.health_updates_thread.start()

    def stop(self) -> None:
        """Stops the running thread, if active."""
        try:
            self.health_updates_thread.do_run = False
        except Exception:
            pass

    def _updates_logic(self, time_to_run: TimeInterval) -> None:
        """
        Starts an infinite loop that runs health checks during time_to_run.
        """
        self.info_process('Starting health checks thread')
        checks_completed = []
        while getattr(threading.current_thread(), "do_run", True):

            # Wait for 6PM to run health checks
            if not time_to_run.contains_time(self.live_time_env.now()):
                checks_completed = []
                pytime.sleep(5)
                continue

            # TODO Ensure we have a valid auth token for the API

            expected_update_time = self.live_time_env.now()

            # Check MongoDB health
            if 'mongo' not in checks_completed:
                self.info_process('Running scheduled mongo model_type')
                # TODO Call API '/api/health_checks/perform?check_type=MONGO'
                # TODO Wait 1 second between /get calls, until last_updated > expected_update_time
                checks_completed.append('mongo')
                continue

            # Check output of dip45 analysis model
            if 'dip45' not in checks_completed:
                self.info_process('Running scheduled dip45 model_type')
                # TODO Call API '/api/health_checks/perform?check_type=DIP45'
                # TODO Wait 1 second between /get calls, until last_updated > expected_update_time
                checks_completed.append('dip45')
                continue

            # Check speed of simulations
            if 'sim-timings' not in checks_completed:
                self.info_process('Running scheduled simulations model_type')
                # TODO Call API '/api/health_checks/perform?check_type=SIMULATION_TIMINGS'
                # TODO Wait 1 second between /get calls, until last_updated > expected_update_time
                checks_completed.append('sim-timings')
                continue

            # Check health of daily data collection and model feeding
            if 'model-feeding' not in checks_completed:
                self.info_process('Running scheduled model feeding check')
                # TODO Call API '/api/health_checks/perform?check_type=MODEL_FEEDING'
                # TODO Wait 1 second between /get calls, until last_updated > expected_update_time
                checks_completed.append('model-feeding')
                continue

            # Check depth and accuracy of symbol data
            for symbol in self.symbols:
                if f'data-{symbol}' not in checks_completed:
                    self.info_process('Running scheduled symbol ({0}) model_type'.format(symbol))
                    # TODO Call API '/api/health_checks/perform?check_type=DATA?symbol={}'
                    # TODO Wait 1 second between /get calls, until last_updated > expected_update_time
                    checks_completed.append('data-' + symbol)
                    break

            # Allow health checks to run again once all have been run
            checks_completed = []
