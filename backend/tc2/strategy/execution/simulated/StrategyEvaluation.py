import statistics
from typing import List

from tc2.strategy.execution.StrategyRun import StrategyRun


class StrategyEvaluation:
    """
    Aggregates all the StrategyExecution results simulated for a historical day.
    Each next StrategyEvaluation can then combine() its results into the next day's StrategyEvaluation.
    """

    def __init__(self, attempts: List[StrategyRun]) -> None:
        """
        Inits this evaluation instance with a list of profits and a days_viable variable (1 or 0).
        :param attempts: a list of executions that may have profited, lost, or not been entered
        """
        # Create variables to be calculated later
        self.days_entered = 0
        self.days_viable = 0
        self.days_evaluated = 1

        # Extract a list of profits (both positive and negative) from the list of attempts
        self.num_attempts = len(attempts)
        self.profits = []
        for execution in attempts:
            if execution.became_viable:
                self.days_viable = 1
            if execution.sell_price is None:
                continue
            profit = (execution.sell_price - execution.buy_price) / execution.buy_price
            self.profits.append(profit)

    def _calculate_metrics(self) -> None:
        # The average profit made from a round-trip trade
        self.avg_profit = sum(self.profits) / max(1, len(self.profits))
        # The median profit made from a round-trip trade
        self.med_profit = 0 if len(self.profits) == 0 else statistics.median(self.profits)
        # The total profit made from a day of trading
        self.net_profit = sum(self.profits)
        # The number of attempts per day at entering a positions
        self.daily_entry_attempts = self.num_attempts
        # The number of round-trip trades made per day
        self.daily_round_trips = len(self.profits) / self.days_evaluated
        # The ratio of positions entered to entry attempts made
        self.entry_ratio = len(self.profits) / max(1, self.num_attempts)
        # The ratio of winning trades to losing trades
        self.win_ratio = len([x for x in self.profits if x > 0]) / max(1, len([x for x in self.profits if x <= 0]))

    def combine(self, next_evaluation: 'StrategyEvaluation') -> None:
        """
        This StrategyEvaluation (self) is the product of each previous StrategyEvaluation combine()-ing with the next.
        This assumes that evaluation window starts with the oldest data and moves to the most recent.
        :param next_evaluation: the StrategyEvaluation result of the latest 1-day simulation window
        """

        # Combine the next evaluation's data into this evaluation's data
        self.days_evaluated += 1
        if len(next_evaluation.profits) / max(1, next_evaluation.num_attempts) > 0:
            self.days_entered += 1
        self.days_viable += next_evaluation.days_viable
        self.profits.extend(next_evaluation.profits)
        self.num_attempts += next_evaluation.num_attempts

        # Re-calculate metrics using the aggregated data
        self._calculate_metrics()
