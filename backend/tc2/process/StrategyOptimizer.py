import random
import time as pytime
from datetime import timedelta, datetime
from typing import Dict, List

from tc2.data.stock_data_collection.ModelFeeder import ModelFeeder
from tc2.data.stock_data_collection.PolygonDataCollector import PolygonDataCollector
from tc2.env.EnvType import EnvType
from tc2.env.ExecEnv import ExecEnv
from tc2.env.TimeEnv import TimeEnv
from tc2.log.LogFeed import LogFeed
from tc2.data.data_storage.mongo.MongoManager import MongoManager
from tc2.data.data_storage.redis.RedisManager import RedisManager
from tc2.strategy.AbstractStrategy import AbstractStrategy
from tc2.strategy.execution.simulated.StrategyEvaluator import StrategyEvaluator
from tc2.util import candle_util
from tc2.env.Settings import Settings
from tc2.util.data_constants import START_DATE
from tc2.util.market_util import OPEN_TIME
from tc2.util.strategy_util import create_day_strategies

# Whether or not to print logs from StrategyOptimizer's simulations
LOG_SIMULATED_STRATEGIES = True

# Strategy optimization enabled/disabled
ENABLED = False

# The number of days on which to train analysis models before simulating strategies
OPTIMIZATION_WARMUP_DAYS = 30


class StrategyOptimizer(ExecEnv):
    """
    Logic loop that evaluates all strategies on all symbols and decides the optimal
    weights each strategy should use for each model.
    """

    strategies: List[AbstractStrategy]

    def __init__(self, creator_env: ExecEnv, logfeed_optimization: LogFeed) -> None:
        super().__init__(creator_env.logfeed_program, logfeed_optimization, creator_env=creator_env)

        # Private variables
        self.running = True

    def start(self) -> None:
        """Runs the program's strategy optimization logic until stop() is called."""

        # Fork the execution environment so it can run in this thread
        self.fork_new_thread()

        # Create strategy objects
        self.strategies = create_day_strategies(self)

        # Turn the process into a control loop that runs evaluations
        while self.running:
            # Wait for user to enable strategy optimization
            if not ENABLED:
                pytime.sleep(5)
                continue

            # Wait for data collector to load data
            if not self.is_data_loaded():
                pytime.sleep(2)
                if random.randint(0, 100) < 30:
                    self.info_process('StrategyOptimizer waiting for historical data to load')
                continue

            # Get the least recently optimized symbol and strategy
            optimization_times = self.get_optimization_times()
            oldest_symbol, oldest_strategy, oldest_time = None, None, self.time().now()
            for symbol in optimization_times.keys():
                for strategy, last_eval_time in optimization_times[symbol].items():
                    if last_eval_time < oldest_time:
                        oldest_symbol, oldest_strategy, oldest_time = symbol, strategy, last_eval_time

            # Run strategy execution simulations and evaluate them
            self.optimize_strategy(oldest_strategy, oldest_symbol)

            # Mark the (strategy, symbol) pair as recently evaluated
            self.redis().set_optimization_time(oldest_symbol, oldest_strategy.__class__.__name__,
                                               self.time().now())

            # Wait a moment before evaluating the next strategy
            pytime.sleep(1)

    def get_optimization_times(self) -> Dict[str, Dict[AbstractStrategy, datetime]]:
        """
        :return: a dictionary like {'TXN': {CycleStrategy: datetime}, ...}
        """
        symbols = {}
        for symbol in Settings.get_symbols(self):
            symbol_strategy_times = {}
            # Each key in the dictionary to return is a symbol name
            for strategy in self.strategies:
                # Get the last eval time for (symbol, strategy)
                symbol_strategy_times[strategy] = self.redis().get_optimization_time(
                    symbol, strategy.__class__.__name__)
                # Each entry in the dictionary to return is a Dict[AbstractStrategy, datetime]
                symbols[symbol] = symbol_strategy_times
        return symbols

    def optimize_strategy(self, strategy: AbstractStrategy, symbol: str) -> None:
        """
        Runs simulations from START_DATE thru two days ago.
        Tries hundreds of model scoring systems and picks the highest performing one.
        """
        self.info_process(f'Optimizing {strategy.__class__.__name__}\'s weights using symbol: {symbol}')
        end_date = self.time().now() - timedelta(days=2)
        dates_on_file = self.mongo().get_dates_on_file(symbol, START_DATE, end_date)
        start_index = OPTIMIZATION_WARMUP_DAYS
        if len(dates_on_file) < start_index + 3:
            self.warn_process(f'Insufficient historical data ({len(dates_on_file)} days) for {symbol}')
            return
        evaluation = None

        # Initialize objects that make up a kind of container for this evaluation
        sim_time_env = TimeEnv(datetime.combine(dates_on_file[start_index - 1], OPEN_TIME))
        sim_env = ExecEnv(self.logfeed_program, self.logfeed_process)
        sim_env.setup_first_time(env_type=EnvType.OPTIMIZATION,
                                 time=sim_time_env,
                                 data_collector=PolygonDataCollector(logfeed_program=self.logfeed_program,
                                                                     logfeed_process=self.logfeed_process,
                                                                     time_env=sim_time_env),
                                 mongo=MongoManager(self.logfeed_program, EnvType.OPTIMIZATION),
                                 redis=RedisManager(self.logfeed_process, EnvType.OPTIMIZATION))

        # Create a ModelFeeder for the simulated environment
        sim_model_feeder = ModelFeeder(sim_env)

        # Place the strategy in the simulated environment
        strategy = self._clone_strategy(strategy, sim_env)

        # Copy data we need from live environment into simulated environment
        data_copy_error = candle_util.init_simulation_data(live_env=self,
                                                           sim_env=sim_env,
                                                           symbols=[strategy.get_symbol()],
                                                           days=start_index - 2,
                                                           end_date=dates_on_file[start_index - 1],
                                                           model_feeder=sim_model_feeder)
        if data_copy_error is not None:
            self.warn_process(data_copy_error)
            return

        for day_to_eval in dates_on_file[start_index:len(dates_on_file) - 2]:
            # Cancel simulations part-way through if a stop has been requested
            if not self.running:
                return

            # Copy day's data into the simulated environment but don't train analysis models
            data_copy_error = candle_util.init_simulation_data(live_env=self,
                                                               sim_env=sim_env,
                                                               symbols=[strategy.get_symbol()],
                                                               days=2,
                                                               end_date=dates_on_file[start_index - 1],
                                                               model_feeder=sim_model_feeder,
                                                               skip_last_day_training=True)
            if data_copy_error is not None:
                self.warn_process(data_copy_error)
                self.warn_process(f'Optimization of {strategy.__class__.__name__} on '
                                  f'{symbol} failed because the program is missing data on {day_to_eval:%Y-%m-%d}')

            # Move the perspective to the historical day
            sim_env.time().set_moment(datetime.combine(day_to_eval, strategy.times_active().get_start_time()))

            # Create a new strategy for this run
            strategy = self._clone_strategy(strategy, sim_env)

            # Run evaluation on the day
            # TODO Change this to run an optimization simulation
            next_evaluation = StrategyEvaluator(strategy).evaluate()

            # Merge the results with all the evaluations from previous days
            if evaluation is None:
                evaluation = next_evaluation
                evaluation._calculate_metrics()
            else:
                evaluation.combine(next_evaluation)

        # Print results after evaluating each day
        if evaluation is not None:
            self.warn_process(
                'Evaluation results of {0} for {1}:\n\t total days = {2}, viable days: {3}, pct days entered = {4}%, '
                'avg profit = {5}, \n\tmedian profit = {6}, win ratio = {7}, entry-attempt ratio = {8}'
                    .format(strategy.__class__.__name__, symbol, evaluation.days_evaluated, evaluation.days_viable,
                            (100 * evaluation.days_entered / evaluation.days_evaluated), evaluation.avg_profit,
                            evaluation.med_profit, evaluation.win_ratio, evaluation.entry_ratio))

        return

    def _clone_strategy(self, original_strategy: AbstractStrategy, sim_env: ExecEnv) -> AbstractStrategy:
        """
        Instantiates a strategy object and places it in a simulated environment.
        """
        strategy_copy = original_strategy.__class__(env=sim_env,
                                                    symbols=original_strategy.get_symbols())

        return strategy_copy

    def stop(self) -> None:
        """Closes any sub-threads and tells the evaluation logic loop to halt."""
        self.running = False
