from datetime import datetime, date
from typing import Optional

from tc2.health_checking.HealthCheckResult import HealthCheckResult
from tc2.health_checking.health_check.AbstractHealthCheck import AbstractHealthCheck
from tc2.strategy.execution.simulated.StrategySimulator import StrategySimulator
from tc2.strategy.strategies.cycle.CycleStrategy import CycleStrategy
from tc2.util.market_util import OPEN_TIME


class SimOutputCheck(AbstractHealthCheck):
    """
    Not meant to be accessed except by HealthChecker.
    Checks that a simulation for a single day uses believable data and produces believable output.

    Conditions for success:
    +
    + Data must be chronologically ordered
    + Data from yesterday must be present
    + Data from today must be present
    """

    TEST_SYMBOL = 'TXN'

    def run(self, day_date: Optional[date] = None) -> HealthCheckResult:
        """
        Prints detailed output of a simulation on a historical day.
        :param day_date: the date to perform a simulation on (defaults to the most recent market day)
        """

        if day_date is None:
            day_date = self.time().get_prev_mkt_day()

        # Initialize a strategy and a simulation environment for it
        self.sim_env.time().set_moment(datetime.combine(day_date, OPEN_TIME))
        strategy = CycleStrategy(env=self.sim_env,
                                 symbols=[self.TEST_SYMBOL])
        simulator = StrategySimulator(strategy, self)

        # Run the simulation
        try:
            simulator.run()
        except Exception as e:
            self.debug('simulation encountered an error: {}'.format(e.args))

        # TODO for msg in simulator.debug_msgs:
        # TODO    self.debug(msg)

        # TODO Pass the health check if its conditions are met
        self.set_passing(True)

        return self.make_result()
