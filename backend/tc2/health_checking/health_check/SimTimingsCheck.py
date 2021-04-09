import time as pytime
from datetime import timedelta, datetime

from tc2.health_checking.HealthCheckResult import HealthCheckResult
from tc2.health_checking.health_check.AbstractHealthCheck import AbstractHealthCheck
from tc2.strategy.execution.simulated.StrategySimulator import StrategySimulator
from tc2.strategy.strategies.cycle.CycleStrategy import CycleStrategy
from tc2.util.data_constants import MIN_CANDLES_PER_DAY
from tc2.util.date_util import DATE_FORMAT
from tc2.util.market_util import OPEN_TIME


class SimTimingsCheck(AbstractHealthCheck):
    """
    Not meant to be accessed except by HealthChecker.
    Checks for any bottleneck points during the simulation process.

    Conditions for success:
    +
    + Simulating a single day takes less than 5 seconds on average.
    """

    TEST_SYMBOL = 'TXN'
    # Number of days to simulate
    SAMPLE_SIZE = 5
    # Max desired time required to simulate a day, in seconds
    MAX_SIMULATION_TIME = 5

    def run(self) -> HealthCheckResult:
        """
        Record average time of simulations using new simulations class in a mock env
        """
        dates = self.mongo().get_dates_on_file(symbol=self.TEST_SYMBOL,
                                               start_date=(self.time().now() - timedelta(
                                                   days=self.SAMPLE_SIZE * 1.3 + 5)).date(),
                                               end_date=(self.time().now() - timedelta(days=1)).date())

        if len(dates) < self.SAMPLE_SIZE:
            self.debug('not enough recent historical data to perform simulations')
            self.set_passing(False)
            return self.make_result()

        sim_durations = []
        for i in range(self.SAMPLE_SIZE):
            # Load historical data to perform a simulation on
            day_date = dates[-i]
            day_data = self.mongo().load_symbol_day(self.TEST_SYMBOL, day_date)
            if len(day_data.candles) < MIN_CANDLES_PER_DAY:
                self.debug('missing data on {0}. can\'t simulate'.format(day_date.strftime(DATE_FORMAT)))
                self.SAMPLE_SIZE += 1
                continue
            prev_day_date = day_date
            prev_day_data = self.mongo().load_symbol_day(self.TEST_SYMBOL,
                                                         prev_day_date - timedelta(days=1))
            while len(prev_day_data.candles) < MIN_CANDLES_PER_DAY:
                prev_day_date -= timedelta(days=1)
                prev_day_data = self.mongo().load_symbol_day(self.TEST_SYMBOL,
                                                             prev_day_date - timedelta(days=1))

            # Initialize a strategy and a simulation environment for it
            self.sim_env.time().set_moment(datetime.combine(day_date, OPEN_TIME))
            strategy = CycleStrategy(env=self.sim_env,
                                     symbols=[self.TEST_SYMBOL])
            simulator = StrategySimulator(strategy, self)

            # Compile data and perform a single simulation with it
            data = list(prev_day_data.candles)
            data.extend(day_data.candles)
            start_instant = pytime.monotonic()
            simulator.run()  # TODO Also record the time of each moment (using optional keyword argument in run())
            sim_duration = pytime.monotonic() - start_instant
            sim_durations.append(sim_duration)
            self.debug('{0} simulation took {1}s'.format(day_date.strftime(DATE_FORMAT), '%.2f' % sim_duration))

        # Calculate average time of each step in the simulation logic
        avg_total_time = sum(sim_durations) / max(1, len(sim_durations))

        # Pass the health check if its conditions are met
        self.set_passing(True)
        if avg_total_time > self.MAX_SIMULATION_TIME:
            self.set_passing(False)

        return self.make_result()
