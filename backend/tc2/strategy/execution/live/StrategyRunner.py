import time as pytime
import traceback
from datetime import timedelta

from tc2.account import AbstractAccount
from tc2.account.data_stream.StreamUpdateType import StreamUpdateType
from tc2.env.ExecEnv import ExecEnv
from tc2.strategy.AbstractStrategy import AbstractStrategy
from tc2.strategy.execution.StrategyRun import StrategyRun


class StrategyRunner(ExecEnv):
    """
    Runs a Strategy instance on live data using a live implementation of AbstractAccountManager.
    """

    # The maximum number of strategy updates to process during one loop iteration
    MAX_UPDATES = 10

    strategy: AbstractStrategy

    def __init__(self, strategy: AbstractStrategy) -> None:
        super().__init__(strategy.logfeed_program, strategy.logfeed_process)
        self.clone_same_thread(strategy)

        self.strategy = strategy

    def run(self, acct: AbstractAccount) -> StrategyRun:
        """
        CAREFUL: Make sure to check that strategy.is_viable() before executing it here.
        Runs the strategy's buy/sell logic on every new candle or order status update,
            until strategy.stop_running() is called.
        """

        # Start execution by giving the strategy data updates to respond to
        self.strategy.provide_account(acct)

        # Run strategy logic when new info comes out of the account listener
        while self.strategy.is_running():

            # Check to force-stop the strategy if it runs past the market closing time
            if not self.time().is_open() and self.strategy.is_running():
                self.strategy.warn_process(f'StrategyRunner force stopping {self.strategy.__class__.__name__} '
                                           f'since it continued after markets closed.')
                self.strategy.warn_main(f'StrategyRunner force stopping {self.strategy.__class__.__name__} '
                                        f'since it continued after markets closed.')
                self.strategy.stop_running(sell_price=None)

            # Feed the strategy trading updates.
            else:
                updates_processed = 0.0
                update = None
                try:
                    # Wait half a second before processing the next batch of updates.
                    pytime.sleep(0.5)
                    # Get first update in the next batch.
                    update_get_start = pytime.monotonic()
                    update = acct.get_next_trading_update(self.strategy.get_symbols(),
                                                          self.strategy.run_info.strategy_start_time)
                    update_get_time_ms = (pytime.monotonic() - update_get_start) * 1000.0
                    if update_get_time_ms > 350:
                        print(f'Took {update_get_time_ms:.0f}ms to get first update in batch')
                except Exception as e:
                    self.error_process(f'Error fetching next data update for strategy:')
                    self.warn_process(f'{traceback.format_exc()}')
                if update is None:
                    print(f'Waiting 0.5s for next update')
                elif update.update_type is StreamUpdateType.CANDLE:
                    print(f'Strategizing on {update.get_symbol()} {update.update_moment:%M:%S} update at '
                          f'{self.strategy.time().now():%M:%S_%f}')
                else:
                    print(f'Strategizing on non-data update')

                # Process several updates consecutively.
                while update is not None and self.strategy.is_running() and updates_processed < self.MAX_UPDATES:
                    updates_processed += 0.05
                    try:
                        # Ignore old updates.
                        if update.update_moment < self.strategy.time().now() - timedelta(seconds=7):
                            print(f'Ignoring old update from {update.update_moment:%M:%S} (now:'
                                  f' {self.strategy.time().now():%M:%S_%f})')
                            update = acct.get_next_trading_update(self.strategy.get_symbols(),
                                                                  self.strategy.run_info.strategy_start_time)
                            continue
                        print(f'SENDING UPDATE TO STRATEGY ({str(update.update_id)})')

                        # Send the update to the strategy.
                        updates_processed += 0.95
                        self.strategy.on_new_info(
                            symbol=update.get_symbol(),
                            moment=update.update_moment,
                            candle=None if update.update_type is not StreamUpdateType.CANDLE else update.get_candle(),
                            order=None if update.update_type is not StreamUpdateType.ORDER else update.get_order())
                    except Exception as e:
                        self.strategy.error_process('Error executing strategy logic:')
                        self.warn_process(traceback.format_exc())
                    update = acct.get_next_trading_update(self.strategy.get_symbols(),
                                                          self.strategy.run_info.strategy_start_time)

        # After execution, cleanup open orders and positions
        acct.cancel_open_orders(symbols=self.strategy.get_symbols())
        acct.liquidate_positions(symbols=self.strategy.get_symbols())

        # Compile the results into a StrategyRun object
        return self.strategy.run_info
