import math
import random
import time as pytime
import traceback
from statistics import mean
from typing import List, Dict, Optional

from tc2.account.AlpacaAccount import AlpacaAccount
from tc2.account.data_stream.StreamUpdateQueue import StreamUpdateQueue
from tc2.env.ExecEnv import ExecEnv
from tc2.env.Settings import Settings
from tc2.log.LogFeed import LogFeed
from tc2.strategy.AbstractStrategy import AbstractStrategy
from tc2.strategy.execution.live.StrategyRunner import StrategyRunner
from tc2.util.Config import BrokerEndpoint
from tc2.util.strategy_util import create_day_strategies, create_swing_strategies


class SymbolStrategyPair:
    """A combination of a strategy and a symbol that can be traded."""
    symbol: str
    strategy: AbstractStrategy

    def __init__(self, symbol: str, strategy: AbstractStrategy):
        self.symbol = symbol
        self.strategy = strategy

    def __str__(self) -> str:
        return self.strategy.get_id() + '_' + self.symbol


# Live day-trading enabled/disabled
DAY_TRADING_ENABLED = True

# Live swing-trading enabled/disabled
SWING_TRADING_ENABLED = True


class LiveTrader(ExecEnv):
    """The controller that chooses which strategies to execute when the markets are open."""

    account: AlpacaAccount
    day_trader: bool
    running: bool
    strategy: Optional[AbstractStrategy]

    def __init__(self, creator_env: ExecEnv,
                 logfeed_trading: LogFeed,
                 day_trader: bool) -> None:
        super().__init__(creator_env.logfeed_program, logfeed_trading, creator_env=creator_env)

        # Public variables
        self.day_trader = day_trader

        # Private variables
        self.running: bool = True
        self.strategy = None

    def start(self,
              livestream_updates: 'multiprocessing list') -> None:
        """Runs the program's live trading logic until stop() is called."""

        self.info_process(f'Starting {self._pref()} logic loop')

        # Fork the execution environment so it can run in this thread
        self.fork_new_thread()

        # Create an account manager for day trading
        self.account = AlpacaAccount(self, self.logfeed_process, livestream_updates)

        # Turn the process into a control loop that live trades during market hours
        while self.running:
            try:
                self.heartbeat()
            except Exception as e:
                self.error_process(f'Error executing {self._pref()} heartbeat:')
                self.warn_process(f'{traceback.format_exc()}')

        self.info_process(f'{self._pref()} logic loop exited')

    def heartbeat(self) -> None:
        """
        The live trading logic to run on a continuous loop.
        """
        if not self.day_trader and self.strategy is None:
            # TODO Continue executing swing strategy from yesterday
            pass

        if self.day_trader and self.strategy is None:
            # Dump order and positions associated with day trading.
            # TODO self._cancel_orders_and_positions()
            pass

        # Wait for user to enable live trading.
        if (self.day_trader and not DAY_TRADING_ENABLED) or (not self.day_trader and not SWING_TRADING_ENABLED):
            pytime.sleep(5)
            if random.randint(0, 100) < 10:
                self.info_process(f'{self._pref()} waiting for user to enable '
                                  f'{"day" if self.day_trader else "swing"} trading')
            return

        # Wait while historical data is still being fetched.
        if not self.is_data_loaded():
            pytime.sleep(2)
            if random.randint(0, 100) < 15:
                self.info_process(f'{self._pref()} waiting for historical data to load')
            return

        # Wait if there's nothing to monitor or start.
        if self.strategy is None and not self.time().is_open():
            pytime.sleep(5)
            if random.randint(0, 100) < 5:
                self.debug_process(f'{self._pref()} waiting for markets to open')
            return

        # Ensure day trading is allowed by the brokerage account.
        if self.day_trader and not self.account.can_day_trade():
            self.warn_process('Cannot execute strategies live. Made too many day trades')
            pytime.sleep(60 * 10)
            return

        # Find strategies that run during this time.
        all_strategies = create_day_strategies(self) if self.day_trader else create_swing_strategies(self)
        all_strategies = [strategy for strategy in all_strategies if not strategy.is_experimental()]
        available_strategies = []
        current_time = self.time().now().time()
        for strategy in all_strategies:
            if strategy.times_active().contains_time(current_time) \
                    and strategy.times_active().will_contain_for(current_time).total_seconds() > 30:
                available_strategies.append(strategy)

        if len(available_strategies) == 0:
            self.debug_process(f'No {"day" if self.day_trader else "swing"} strategies allowed to run now')
            pytime.sleep(30)
            return
        else:
            self.info_process(f'{"Day" if self.day_trader else "Swing"} strategies '
                              f'allowed to run now (ordered by priority): '
                              f'{", ".join([strat.get_id() for strat in available_strategies])}')

        # Find all viable (symbol, strategy) pairs.
        viable_pairs = []
        try:
            for strategy in available_strategies:
                # Filter out symbols that fail the strategy's viability tests.
                # self.debug_process(f'scoring symbols for {strategy.get_id()}')
                viable_symbols = strategy.score_symbols()
                # self.debug_process(f'scored symbols for {strategy.get_id()}')
                for symbol in viable_symbols:
                    viable_pairs.append(SymbolStrategyPair(symbol, strategy))
                # self.debug_process(f'added viable symbols for {strategy.get_id()}')

                # Log viable symbols for this strategy.
                self.info_process('Viable symbols for {}: {}'.format(
                    strategy.get_id(),
                    viable_symbols if len(viable_symbols) > 0 else 'none'
                ))
        except Exception as e:
            self.error_process(f'Could not check strategy viability: {traceback.format_exc()}')

        # Stop trying to trade if there are no viable symbols for any available strategy.
        if len(viable_pairs) == 0:
            self.debug_process(f'No {"day" if self.day_trader else "swing"} strategies viable now')
            pytime.sleep(30)
            return

        # Select the (symbol, strategy) pair that has performed best in the past.
        best_pair = self.choose_best_viable_pair(viable_pairs)
        strategy = best_pair.strategy
        strategy.set_symbols([best_pair.symbol])
        if strategy.get_id().lower().__contains__('longshortstrategy'):
            self.warn_process(f'Resetting account: clearing orders, positions, and cache')
            strategy.set_symbols(['SPY', 'SPXL', 'SPXS'])
            pytime.sleep(3)
            self.account.cancel_open_orders(['SPXL', 'SPXS'])
            pytime.sleep(3)
            self.account.liquidate_positions(['SPXL', 'SPXS'])
            pytime.sleep(30)
            self.account.refresh_open_orders(['SPXL', 'SPXS'])
            pytime.sleep(5)
            self.account.refresh_positions(['SPXL', 'SPXS'])
            pytime.sleep(5)
            symbols_held = [position.symbol for position in self.account.get_positions()]
            self.warn_process(f'Symbols held: {", ".join(symbols_held)}')
            if any(symbol in symbols_held for symbol in ['SPXS', 'SPXL']):
                self.warn_process(f'SPXL or SPXS positions still held. Can\'t start LongShortStrategy!')
                return

        # Execute the strategy.
        self.account.stream_queue = StreamUpdateQueue()
        self.info_process(f'{self._pref()} executing {strategy.get_id()} on '
                          f'{self.time().now():%Y-%m-%d} at {self.time().now():%H:%M:%S}')
        runner = StrategyRunner(strategy)
        live_run = runner.run(self.account)
        self.info_process(f'{self._pref()} finished executing {strategy.get_id()} on '
                          f'{self.time().now():%Y-%m-%d} at {self.time().now():%H:%M:%S}')

        # Save strategy run data in redis.
        self.redis().record_live_run(strategy_id=strategy.get_id(),
                                     run=live_run,
                                     endpoint=Settings.get_endpoint(self))

        # Before executing the next strategy, wait for account balance to update.
        pytime.sleep(2)

    def choose_best_viable_pair(self, viable_pairs: List[SymbolStrategyPair]) -> SymbolStrategyPair:
        """
        Selects the most promising symbol, balancing past profits, entry ratio, and volume of run data.
        """

        # Use a points system to rank pairs.
        scores: Dict[SymbolStrategyPair, float] = {}
        for pair in viable_pairs:
            scores[pair] = 0

            # Load strategy history for this pair.
            strategy_runs = self.redis().get_live_run_history(
                strategies=[pair.strategy.get_id()],
                paper=True if Settings.get_endpoint(self) == BrokerEndpoint.PAPER else False,
                symbols=[pair.symbol]
            )
            finished_runs = [run for run in strategy_runs
                             if sum([sum(symbol_run.sell_prices) for symbol_run in run.symbol_runs]) > 0]

            # Reward symbol score for previous profitable runs.
            # FORMULA:   2(log(x) + 2)       (i.e. avg_profit in [0.01, 2] -> points in [0, 4.5]).
            positive_profits = []

            # Iterate through each historical trade.
            for run in finished_runs:
                for symbol_run in run.symbol_runs:
                    for i in range(len(symbol_run.times_bought)):

                        # Ensure we have records of buy/sell/qties for this index (i.e. the trade was completed).
                        if i >= len(symbol_run.qties_traded) or i >= len(symbol_run.times_sold):
                            continue

                        # Determine whether this was a long or short trade.
                        long_order = symbol_run.qties_traded[i] > 0

                        # Calculate profit of previous long trade.
                        if long_order and symbol_run.buy_prices[i] < symbol_run.sell_prices[i]:
                            positive_profits.append(
                                (symbol_run.sell_prices[i] - symbol_run.buy_prices[i]) / symbol_run.buy_prices[i])

                        # Calculate profit of previous short trade.
                        elif not long_order and symbol_run.sell_prices[i] > symbol_run.buy_prices[i]:
                            positive_profits.append(
                                (symbol_run.buy_prices[i] - symbol_run.sell_prices[i]) / symbol_run.sell_prices[i])

            # Add to symbol score based on average historical profit percent.
            avg_positive_profit = 0 if len(positive_profits) == 0 else \
                mean(positive_profits) / len(positive_profits)
            x = min(2.0, max(0.01, avg_positive_profit))
            scores[pair] += max(0.0, 2 * (math.log(x, 10) + 2))

            # Penalize symbol score for history of losses.
            # Formula: -4(log(x) + 2)     (i.e. avg_loss in [0.01, 2] -> points in [0, 9]).
            negative_profits = []

            # Iterate through each historical trade.
            for run in finished_runs:
                for symbol_run in run.symbol_runs:
                    for i in range(len(symbol_run.times_bought)):

                        # Ensure we have records of buy/sell/qties for this index (i.e. the trade was completed).
                        if i >= len(symbol_run.qties_traded) or i >= len(symbol_run.times_sold):
                            continue

                        # Determine whether this was a long or short trade.
                        long_order = symbol_run.qties_traded[i] > 0

                        # Calculate loss of previous long trade.
                        if long_order and symbol_run.buy_prices[i] > symbol_run.sell_prices[i]:
                            negative_profits.append(
                                (symbol_run.buy_prices[i] - symbol_run.sell_prices[i]) / symbol_run.buy_prices[i])

                        # Calculate loss of previous short trade.
                        elif not long_order and symbol_run.sell_prices[i] < symbol_run.buy_prices[i]:
                            negative_profits.append(
                                (symbol_run.sell_prices[i] - symbol_run.buy_prices[i]) / symbol_run.sell_prices[i])

            # Subtract from symbol score based on average historical loss percent.
            avg_loss = 0 if len(negative_profits) == 0 else \
                sum(negative_profits) / len(negative_profits)
            x = min(2.0, max(0.01, avg_loss))
            scores[pair] -= max(0.0, 4 * (math.log(x, 10) + 2))

            # Penalize symbol score for low entry ratio.
            # FORMULA:   -45log(x) + 0.5      (i.e. entry_ratio in [0.05, 1] -> points in [55, 0]).
            entry_ratio = 0 if len(finished_runs) == 0 \
                else len(finished_runs) / len(strategy_runs)
            x = max(0.05, entry_ratio)
            scores[pair] -= max(0.0, -45 * (math.log(x, 10) + 0.5))

            # Randomly penalize symbol score for lack of run history.
            # FORMULA:   -7log(6x) + 16      (i.e. runs_on_file in [1, 25] -> points in [10, 1]).
            if random.randint(1, 100) < 75:
                x = max(1, len(strategy_runs))
                scores[pair] -= max(0.0, -7 * (math.log(x, 10) + 16))

        self.info_process(f'{self._pref()} <symbol, strategy> scores before normalizing: '
                          f'{[str(pair) + ": " + str(score) for pair, score in scores.items()]}')

        # Sort symbols ascending by score
        ascending_symbols = sorted(list(scores.keys()), key=lambda pair: scores[pair])

        # Normalize scores so that their range is [0,100]
        lowest_score = scores[ascending_symbols[0]]
        highest_score = max(1.0, scores[ascending_symbols[-1]]) + abs(lowest_score)
        for pair in scores.keys():
            scores[pair] += abs(lowest_score)
            scores[pair] = 100 * scores[pair] / highest_score

        self.info_process(f'{self._pref()} <symbol, strategy> scores after normalizing: '
                          f'{[str(pair) + ": " + str(score) for pair, score in scores.items()]}')

        # Add more copies of symbols with higher scores (increase their chance of being chosen from the list)
        symbol_lottery = []
        for pair, score in scores.items():
            symbol_lottery.append(pair)
            for i in range(1, int(score) + 1):
                symbol_lottery.append(pair)

        self.info_process(f'{self._pref()} <symbol, strategy> lottery after normalizing: '
                          f'{[str(pair) for pair in symbol_lottery]}')
        return random.choice(symbol_lottery)

    def _pref(self) -> str:
        """Returns 'LiveDayTrader' or 'LiveSwingTrader', according to the process's domain."""
        return 'LiveDayTrader' if self.day_trader else 'LiveSwingTrader'

    def stop(self) -> None:
        """Stops any running strategies."""
        self.running = False
        if self.strategy is not None:
            self.strategy.stop_running(sell_price=None)
