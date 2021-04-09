import traceback
from datetime import timedelta, datetime
from typing import List

from tc2.account.VirtualAccount import VirtualAccount
from tc2.account.data_stream.StreamUpdateType import StreamUpdateType
from tc2.data.stock_data_collection.ModelFeeder import ModelFeeder
from tc2.env.ExecEnv import ExecEnv
from tc2.strategy import AbstractStrategy
from tc2.strategy.execution.StrategyRun import StrategyRun
from tc2.util import candle_util
from tc2.util.market_util import CLOSE_TIME


class StrategySimulator(ExecEnv):
    """
    Runs the same Strategy classes used for live trading, but on historical data using virtual time and a
    VirtualAccount.
    """

    VIRTUAL_BALANCE = 30000

    strategy: AbstractStrategy
    sim_begin: datetime
    live_env: ExecEnv
    all_symbols: List[str]

    def __init__(self,
                 strategy: AbstractStrategy,
                 live_env: ExecEnv,
                 all_symbols: List[str] = None) -> None:
        """
        :param all_symbols: A list of all symbols needed for both trading and viability checks
        """
        super().__init__(strategy.logfeed_program, strategy.logfeed_process)
        self.clone_same_thread(strategy)

        # Private variables
        self.strategy = strategy
        self.sim_begin = self.time().now()
        self.live_env = live_env
        self.all_symbols = all_symbols if all_symbols is not None else strategy.get_symbols()

    def run(self,
            warmup_days: int = 30,
            update_interval: int = 1001) -> StrategyRun:
        """
        Runs a simulation over a single day.
        The default update_interval is 1001 because we use 1-second live candles during live trading.
        :param warmup_days: the number of previous days to train models on before running the simulation
        :param update_interval: the number of ms to jump forward between logic loops
                (in real trading this would be equal to the time between CPU cycles)
        """

        """ I. Load price data into the simulation environment """

        # Collect past data and train models
        self.reset_dbs()

        self.info_process('StrategySimulator warming up {} days to {}/{}/{}'
                          .format(warmup_days,
                                  self.sim_begin.year,
                                  self.sim_begin.month,
                                  self.sim_begin.day))

        # Copy data we need from live environment into simulated environment
        data_copy_error = candle_util.init_simulation_data(live_env=self.live_env,
                                                           sim_env=self,
                                                           symbols=self.all_symbols,
                                                           days=warmup_days,
                                                           end_date=self.time().get_next_mkt_day(
                                                               self.time().now().date()),
                                                           model_feeder=ModelFeeder(self),
                                                           skip_last_day_training=True)
        if data_copy_error is not None:
            self.warn_process(data_copy_error)
            return StrategyRun(symbol_runs=self.strategy.get_symbols(),
                               strategy_start_time=self.sim_begin,
                               strategy_end_time=self.sim_begin,
                               metadata=None)

        # Set the virtual time to the simulation start time
        self.time().set_moment(self.sim_begin)

        """ II. Fast-forward virtual time to the earliest time when the strategy is runnable """

        # Move the virtual time forward to when the strategy can be executed
        if self.time().now() > datetime.combine(self.time().now().date(), self.strategy.times_active().get_end_time()):
            self.warn_process(f'Tried to start a simulation on {self.strategy.get_id()} at '
                              f'{self.time().now().time():%H:%M:%S} but it does not run past '
                              f'{self.strategy.times_active().get_end_time():%H:%M:%S}')
        while not self.strategy.times_active().contains_time(self.time().now()):
            self.incr_time(minutes=3)
            if not self.time().is_open():
                self.warn_main(f'{self.strategy.get_id()} has misconfigured times_active. '
                               f'Can\'t simulate it!')
                return StrategyRun(symbol_runs=self.strategy.get_symbols(),
                                   strategy_start_time=self.sim_begin,
                                   strategy_end_time=CLOSE_TIME,
                                   metadata=None)
        self.strategy.run_info.start_time = self.time().now()
        self.info_process(f'DEBUG: StrategySimulator fast-forwarded to {self.time().now()}')

        """ III. Execute the strategy """
        # Now that our virtual time is an active time for the strategy, we can execute it
        self.debug_process(f'StrategySimulator starting simulation on {self.time().now().date()} at '
                           f'{self.time().now().time()}')
        try:
            return self._simulate(update_interval)
        except Exception as e:
            self.error_process('Error simulating strategy:')
            self.warn_process(traceback.format_exc())
            return self.strategy.run_info

    def _simulate(self, update_interval: int) -> StrategyRun:
        """
        Gives the strategy an account and data to use, waits for the symbol to become viable, and then
        executes the strategy. The result of the execution is returned.
        """

        # Create a virtual account with virtual balance
        acct = VirtualAccount(sim_env=self,
                              logfeed_process=self.logfeed_process,
                              start_time=self.strategy.run_info.start_time)
        acct.balance = StrategySimulator.VIRTUAL_BALANCE
        acct.withdrawable_balance = StrategySimulator.VIRTUAL_BALANCE
        self.strategy.provide_account(acct)

        # Init viability check variables
        viability_check_incr = timedelta(seconds=30)
        self.time().set_moment(self.time().now() - viability_check_incr)
        strategy_became_viable = False

        # Wait for strategy to become viable (pass all its models)
        while True:

            # Fast forward 30 seconds
            self.time().set_moment(self.time().now() + viability_check_incr)
            self.strategy.run_info.start_time = self.time().now()

            # Check viability.
            if len(self.strategy.score_symbols(self.strategy.get_symbols())) == 0:
                # If strategy never becomes viable during its run window, cancel simulation.
                if not self.strategy.times_active().contains_time(self.time().now()) \
                        or self.time().now().time() >= CLOSE_TIME:
                    self.strategy.stop_running(sell_price=None)
                    self.info_process(f'{self.strategy.get_id()} never became viable during its run window')
                    break
                # Else, check again.
                else:
                    continue

            # Exit loop when strategy becomes viable.
            else:
                self.debug_process(f'STRATEGY BECAME VIABLE AT {self.time().now()}')
                strategy_became_viable = True
                self.strategy.run_info.start_time = self.time().now()
                break

        # Now the strategy is viable. Start executing it.

        # Load historical data that was copied into the simulation environment.
        self.debug_process(f'Loading historical data for the simulation')
        symbol_datas = [
            self.mongo().load_symbol_day(symbol=symbol,
                                         day=self.time().now().date())
            for symbol in self.strategy.get_symbols()]
        # self.debug_process(f'simulation data: '
        #                    f'{[day_data.symbol + ": " + str(len(day_data.candles)) + " candles" for day_data in symbol_datas]}')

        # Execute while markets are open and nothing calls strategy.stop_running()
        self.debug_process('Beginning simulated strategy execution')
        while self.strategy.is_running() and self.time().now().time() < CLOSE_TIME:

            # Refresh account info to simulate receiving a message from the stream.
            # This will add new updates to the account's queue.
            for day_data in symbol_datas:
                acct.refresh_acct(self.time().now(), day_data)

            # Run the strategy's logic if a new candle or order is received.
            try:
                update = acct.get_next_trading_update(self.strategy.get_symbols(),
                                                      self.strategy.run_info.strategy_start_time)
                updates_processed = 0
                while update is not None and self.strategy.is_running() and updates_processed < 50:
                    updates_processed += 1
                    self.strategy.on_new_info(
                        symbol=update.get_symbol(),
                        moment=update.update_moment,
                        candle=None if update.update_type is not StreamUpdateType.CANDLE else update.get_candle(),
                        order=None if update.update_type is not StreamUpdateType.ORDER else update.get_order())
                    update = acct.get_next_trading_update(self.strategy.get_symbols(),
                                                      self.strategy.run_info.strategy_start_time)
                if updates_processed > 20:
                    self.warn_process(f'Simulated strategy processed {updates_processed} updates at once '
                                      f'(should be less than 5)')
            except Exception as e:
                self.error_process('Error simulating a strategy:')
                self.warn_process(traceback.format_exc())

            # Move the virtual time forward.
            self.incr_time(milliseconds=update_interval)
            # self.info_process(f'Simulating for {self.time().now():%H:%M:%S}')

        # Force stop the strategy if necessary.
        if self.strategy.is_running():
            self.strategy.stop_running(sell_price=None)

        # Return execution data for the user to see.
        return self.strategy.run_info

    def incr_time(self, milliseconds: int = 0, minutes: int = 0) -> None:
        self.time().set_moment(self.time().now() + timedelta(minutes=minutes, milliseconds=milliseconds))
