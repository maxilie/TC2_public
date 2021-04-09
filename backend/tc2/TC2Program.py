from __future__ import annotations

import os
import time as pytime
import traceback
from datetime import datetime
from multiprocessing import Process
from threading import Thread

from tc2.account.data_stream.AccountDataStream import AccountDataStream
from tc2.data.data_storage.mongo.MongoManager import MongoManager
from tc2.data.data_storage.redis.RedisManager import RedisManager
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.data.stock_data_collection.ModelFeeder import ModelFeeder
from tc2.data.stock_data_collection.PolygonDataCollector import PolygonDataCollector
from tc2.env.EnvType import EnvType
from tc2.env.ExecEnv import ExecEnv
from tc2.env.Settings import Settings
from tc2.env.TimeEnv import TimeEnv
from tc2.log.LogFeed import LogCategory, LogFeed, LogLevel
from tc2.log.Loggable import Loggable
from tc2.process.DailyCollector import DailyCollector
from tc2.process.HealthChecksRefresher import HealthChecksRefresher
from tc2.process.LiveTrader import LiveTrader
from tc2.process.StrategyOptimizer import StrategyOptimizer
from tc2.process.VisualsRefresher import VisualsRefresher
from tc2.util.Config import BrokerEndpoint


class TC2Program(Loggable):
    """
    The backend program, which is initialized by django startup code.
    """

    # Live execution environment.
    live_env: ExecEnv

    # Log feeds.
    logfeed_data: LogFeed
    logfeed_trading: LogFeed
    logfeed_optimization: LogFeed
    logfeed_api: LogFeed
    logfeed_visuals: LogFeed

    # Logic loops (running inside threads).
    strategy_optimizer: StrategyOptimizer
    live_day_trader: LiveTrader
    live_swing_trader: LiveTrader
    daily_collector: DailyCollector
    visuals_refresher: VisualsRefresher
    health_checks_refresher: HealthChecksRefresher

    # Threads (containing logic loops).
    day_trading_process: Process
    swing_trading_process: Process
    optimizations_process: Process
    collection_process: Process

    def __init__(self, logfeed_program):
        super().__init__(logfeed_program, logfeed_program)

    def start_program(self) -> None:
        """
        Loads settings and runs program processes in their own threads.
        This can take several seconds to complete.
        """

        # Log startup.
        self.warn_main('.........')
        self.warn_main('........')
        self.warn_main('.......')
        self.warn_main('......')
        self.warn_main('.....')
        self.warn_main('....')
        self.warn_main('...')
        self.warn_main('..')
        self.warn_main('.')
        self.warn_main('')
        self.warn_main('Program starting...')
        self.warn_main('')
        self.warn_main('.')
        self.warn_main('..')
        self.warn_main('...')
        self.warn_main('....')
        self.warn_main('.....')
        self.warn_main('......')
        self.warn_main('.......')
        self.warn_main('........')
        self.warn_main('.........')

        # Load pre-reqs first.
        try:
            self.info_main('Loading settings from config...')
            self.load_pre_reqs()
            self.info_main('Loaded settings')
        except Exception:
            self.error_main('Failed to load program essentials:')
            self.warn_main(traceback.format_exc())
            self.shutdown()
            return

        # Connect to market data and brokerage account data.
        try:
            self.info_main('Connecting to live data streams')
            self.init_account_data_streams()
            livestream_updates = AccountDataStream._livestream_updates
            self.info_main('Connected to alpaca and polygon streams')
        except Exception:
            self.error_main('Failed to connect to data streams:')
            self.warn_main(traceback.format_exc())
            self.shutdown()
            return

        # Mark data as loading and start a thread to get data and models up to date.
        try:
            self.perform_data_catchup()
        except Exception:
            self.error_main('Failed to start data catch-up task:')
            self.warn_main(traceback.format_exc())
            self.shutdown()
            return

        # Run data collection in its own core, if possible - otherwise, in its own thread.
        try:
            self.info_main('Starting data collection process')
            self.start_daily_collection(livestream_updates)
            self.info_main('Started data collection process')
        except Exception:
            self.error_main('FAILED TO START DATA COLLECTION:')
            self.warn_main(traceback.format_exc())
            self.shutdown()

        # Run live trading in its own core, if possible - otherwise, in its own thread.
        try:
            self.info_main('Starting trading process')
            self.start_live_trading(livestream_updates)
            self.info_main('Started trading process')
        except Exception:
            self.error_main('Failed to start trading logic:')
            self.warn_main(traceback.format_exc())
            self.shutdown()

        # Run strategy optimization in its own core, if possible - otherwise, in its own thread.
        try:
            self.info_main('Starting simulation and evaluation process')
            self.start_strategy_optimization()
            self.info_main('Started simulation and evaluation process')
        except Exception:
            self.error_main('Failed to start strategy parameter optimization logic:')
            self.warn_main(traceback.format_exc())
            self.shutdown()

        # Init manager class and refresher thread for visualization.
        try:
            self.info_main('Initializing visuals (graphs, charts, etc.) generation components')
            self.init_visualization()
            self.info_main('Initialized visualization components')
        except Exception:
            self.error_main('Failed to initialize visualization components:')
            self.warn_main(traceback.format_exc())
            self.shutdown()

        # Init manager class and refresher thread for health checks.
        try:
            self.info_main('Initializing health checker')
            self.init_health_checks()
            self.info_main('Initialized health checker')
        except Exception:
            self.error_main('Failed to initialize health checker')
            self.warn_main(traceback.format_exc())
            self.shutdown()

        self.info_main('Started successfully!')

    def load_pre_reqs(self) -> None:
        # Initialize log feeds.
        self.logfeed_data = LogFeed(LogCategory.DATA)
        self.logfeed_data.log(LogLevel.ERROR, '.             ...PROGRAM RESTARTED...')
        self.logfeed_trading = LogFeed(LogCategory.LIVE_TRADING)
        self.logfeed_trading.log(LogLevel.ERROR, '.             ...PROGRAM RESTARTED...')
        self.logfeed_optimization = LogFeed(LogCategory.OPTIMIZATION)
        self.logfeed_optimization.log(LogLevel.ERROR, '             ...PROGRAM RESTARTED...')
        self.logfeed_visuals = LogFeed(LogCategory.VISUALS)
        self.logfeed_visuals.log(LogLevel.ERROR, '.             ...PROGRAM RESTARTED...')
        self.logfeed_api = LogFeed(LogCategory.API)
        self.logfeed_api.log(LogLevel.ERROR, '.             ...PROGRAM RESTARTED...')

        # Create time environment for live data collection and trading.
        live_time_env = TimeEnv(datetime.now())

        # Create database managers but don't initialize connections.
        live_redis = RedisManager(self.logfeed_program, EnvType.LIVE)
        live_mongo = MongoManager(self.logfeed_program, EnvType.LIVE)

        # Initialize collector manager to access polygon.io.
        live_data_collector = PolygonDataCollector(logfeed_program=self.logfeed_program,
                                                   logfeed_process=self.logfeed_data,
                                                   time_env=live_time_env)

        # Initialize the live execution environment with program logs.
        self.live_env = ExecEnv(logfeed_program=self.logfeed_program,
                                logfeed_process=self.logfeed_program)

        # Setup the live execution environment with live time & data variables.
        self.live_env.setup_first_time(env_type=EnvType.LIVE,
                                       time=live_time_env,
                                       data_collector=live_data_collector,
                                       mongo=live_mongo,
                                       redis=live_redis)

        # Set Alpaca credentials as environment variables so we don't have to pass them around.
        live_trading = True if Settings.get_endpoint(self.live_env) == BrokerEndpoint.LIVE else False
        os.environ['APCA_API_BASE_URL'] = 'https://api.alpaca.markets' \
            if live_trading else 'https://paper-api.alpaca.markets'
        os.environ['APCA_API_KEY_ID'] = self.live_env.get_setting('alpaca.live_key_id') \
            if live_trading else self.live_env.get_setting('alpaca.paper_key_id')
        os.environ['APCA_API_SECRET_KEY'] = self.live_env.get_setting('alpaca.live_secret_key') \
            if live_trading else self.live_env.get_setting('alpaca.paper_secret_key')
        os.environ['POLYGON_KEY_ID'] = self.live_env.get_setting('alpaca.live_key_id')

    def init_account_data_streams(self) -> None:
        AccountDataStream.connect_to_streams(symbols=Settings.get_symbols(self.live_env),
                                             logfeed_data=self.logfeed_data)

    def start_daily_collection(self,
                               livestream_updates: 'multiprocessing list') -> None:
        """
        Starts a multiprocessing.Process, which is basically a Thread that can use its own core.
        Schedules data collection to run (and trigger model feeding) after markets close every day.
        """

        # Daily collector logic loop to schedule daily collection and model feeding.
        self.daily_collector = DailyCollector(self.live_env, self.logfeed_data)

        self.collection_process = Process(target=self.daily_collector.start_collection_loop, args=(livestream_updates,))
        self.collection_process.start()

    def perform_data_catchup(self) -> None:
        """
        Fetches historical data off-thread from Polygon.io, if any is missing.
        """

        # Train models on any data that was missed while the bot was offline.
        catch_up_days = 3

        # Retrain models if the bot has insufficient warm-up data.
        warm_up_days = 27

        def catch_up():
            self.info_main('Trading and simulation disabled while checking for missing recent data...')
            catch_up_start_moment = pytime.monotonic()

            # Fork data_env for the new thread.
            catch_up_env = ExecEnv(self.logfeed_program, self.logfeed_data, creator_env=self.live_env)
            catch_up_env.fork_new_thread()
            catch_up_env.info_process('Performing catch-up task: checking for missing recent data')

            # Fork model feeder for the new thread.
            catch_up_model_feeder = ModelFeeder(catch_up_env)

            # Reset models and go back 31 days if missing [t-31, t-4].
            # OR go back 4 days if only missing at most [t-4, t-1].

            # Start at t-31 days.
            day_date = catch_up_env.time().now().date()
            while not catch_up_env.time().is_mkt_day(day_date):
                day_date = catch_up_env.time().get_prev_mkt_day(day_date)
            for _ in range(warm_up_days + catch_up_days + 1):
                day_date = catch_up_env.time().get_prev_mkt_day(day_date)

            # Check that each day [t-31, t-4] has valid data.
            symbols_reset = []
            for _ in range(warm_up_days):
                # Check the next day.
                day_date = catch_up_env.time().get_next_mkt_day(day_date)

                for symbol in Settings.get_symbols(catch_up_env):
                    # Only check the symbol if it hasn't been reset.
                    if symbol in symbols_reset:
                        continue

                    # Load the day's data and validate it.
                    day_data = catch_up_env.mongo().load_symbol_day(symbol, day_date)
                    if not SymbolDay.validate_candles(day_data.candles):
                        catch_up_env.info_process('{} missing price data on {}. Resetting its model data'
                                                  .format(symbol, day_date))
                        catch_up_model_feeder.reset_models([symbol])
                        symbols_reset.append(symbol)

            # Go back to the latest potential missing day.
            day_date = catch_up_env.time().now().date()
            while not catch_up_env.time().is_mkt_day(day_date):
                day_date = catch_up_env.time().get_prev_mkt_day(day_date)
            for _ in range(warm_up_days + catch_up_days + 1 if len(symbols_reset) != 0 else catch_up_days + 1):
                day_date = catch_up_env.time().get_prev_mkt_day(day_date)

            # Use price data to train models.
            for _ in range(warm_up_days + catch_up_days if len(symbols_reset) != 0 else catch_up_days):

                # Go through each reset symbol.
                for symbol in symbols_reset:

                    # Load mongo price data if present.
                    start_instant = pytime.monotonic()
                    day_data = catch_up_env.mongo().load_symbol_day(symbol, day_date)

                    # Collect polygon-rest price data if necessary.
                    if not SymbolDay.validate_candles(day_data.candles):
                        try:
                            day_data = catch_up_env.data_collector().collect_candles_for_day(day_date, symbol)
                        except Exception as e:
                            catch_up_env.error_process('Error collecting polygon-rest data:')
                            catch_up_env.warn_process(traceback.format_exc())
                    collection_time = pytime.monotonic() - start_instant

                    # Validate data.
                    validation_debugger = []
                    if day_data is not None and SymbolDay.validate_candles(day_data.candles,
                                                                           debug_output=validation_debugger):
                        # Save data
                        catch_up_env.redis().reset_day_difficulty(symbol, day_date)
                        catch_up_env.mongo().save_symbol_day(day_data)

                        # Use data to train models for symbol on day.
                        start_instant = pytime.monotonic()
                        catch_up_model_feeder.train_models(symbol=symbol,
                                                           day_date=day_date,
                                                           day_data=day_data,
                                                           stable=True)
                        train_time = pytime.monotonic() - start_instant
                        catch_up_env.info_process(f'Catch-up for {symbol} on {day_date:%m-%d-%Y}: collection took '
                                                  f'{collection_time:.2f}s;  training took {train_time:.2f}s')
                    else:
                        catch_up_env.redis().incr_day_difficulty(symbol, day_date)
                        catch_up_env.warn_process(f'Couldn\'t collect catch-up data for {symbol} on {day_date}: '
                                                  f'{"null" if day_date is None else len(day_data.candles)} candles')
                        catch_up_env.warn_process('\n'.join(validation_debugger))

                # Move to the next day.
                day_date = catch_up_env.time().get_next_mkt_day(day_date)

            # Determine whether or not we have yesterday's cached data for at least one symbol.
            unstable_data_present = False
            while not catch_up_env.time().is_mkt_day(day_date):
                day_date = catch_up_env.time().get_prev_mkt_day(day_date)
            for symbol in Settings.get_symbols(catch_up_env):
                unstable_data = catch_up_env.redis().get_cached_candles(symbol, day_date)
                if unstable_data is not None and SymbolDay.validate_candles(unstable_data):
                    unstable_data_present = True
                    break

            if unstable_data_present:
                msg = f'Valid cached redis data on {day_date:%B %d} found. ' \
                      f'Models and strategies should function normally'
                catch_up_env.info_main(msg)
                catch_up_env.info_process(msg)
            else:
                msg = f'No valid redis data cached on {day_date:%b %d}. Models that need yesterday\'s data will ' \
                      f'fail, causing some strategies to fail.'
                catch_up_env.warn_main(msg)
                catch_up_env.warn_process(msg)

            # Allow processes to resume now that data_collector is not busy.
            catch_up_env.mark_data_as_loaded()
            msg = f'Trading and strategy optimization enabled (catch up task took ' \
                  f'{(pytime.monotonic() - catch_up_start_moment) / 3600:.2f} hrs)'
            catch_up_env.info_main(msg)
            catch_up_env.info_process(msg)

        data_load_thread = Thread(target=catch_up)
        data_load_thread.start()

    def start_live_trading(self,
                           livestream_updates: 'multiprocessing list') -> None:
        """
        Runs live day- and swing-trading in their own Processes.
        """
        self.live_day_trader = LiveTrader(creator_env=self.live_env,
                                          logfeed_trading=self.logfeed_trading,
                                          day_trader=True)
        self.day_trading_process = Process(target=self.live_day_trader.start, args=(livestream_updates,))
        self.day_trading_process.start()

        self.live_swing_trader = LiveTrader(creator_env=self.live_env,
                                            logfeed_trading=self.logfeed_trading,
                                            day_trader=False)
        self.swing_trading_process = Process(target=self.live_swing_trader.start, args=(livestream_updates,))
        self.swing_trading_process.start()

    def start_strategy_optimization(self) -> None:
        """
        Runs strategy optimization in its own Process.
        """
        self.strategy_optimizer = StrategyOptimizer(creator_env=self.live_env,
                                                    logfeed_optimization=self.logfeed_optimization)
        self.optimizations_process = Process(target=self.strategy_optimizer.start)
        self.optimizations_process.start()

    def init_visualization(self) -> None:
        """
        Schedules visuals to update continuously.
        The user can also update visuals manually using the webpanel.
        """

        # Schedule visuals to continuously update in the background.
        self.visuals_refresher = VisualsRefresher(logfeed_program=self.logfeed_program,
                                                  logfeed_process=self.logfeed_visuals,
                                                  symbols=Settings.get_symbols(self.live_env),
                                                  live_time_env=self.live_env.time())
        self.visuals_refresher.start()

    def init_health_checks(self) -> None:
        """
        Schedules health checks (e.g. data checks, analysis model checks) to run at night.
        The user can also run checks manually using the webpanel.
        """

        # Schedule health checks to run every night.
        self.health_checks_refresher = HealthChecksRefresher(logfeed_program=self.logfeed_program,
                                                             logfeed_process=self.logfeed_program,
                                                             symbols=Settings.get_symbols(self.live_env),
                                                             live_time_env=self.live_env.time())
        self.health_checks_refresher.start()

    def shutdown(self) -> None:
        self.info_main('Shutting down...')

        try:
            # Stop thread that runs health checks.
            self.health_checks_refresher.stop()
        except Exception:
            traceback.print_exc()

        try:
            # Stop thread that generates visuals.
            self.visuals_refresher.stop()
        except Exception:
            traceback.print_exc()

        try:
            # Stop collection process.
            self.daily_collector.stop()
            self.collection_process.terminate()
        except Exception:
            traceback.print_exc()

        try:
            # Close account/market websocket connections.
            AccountDataStream.shutdown()
        except Exception:
            traceback.print_exc()

        try:
            # Stop evaluations process.
            self.strategy_optimizer.stop()
            self.optimizations_process.terminate()
        except Exception:
            traceback.print_exc()

        try:
            # Stop day trading process.
            self.live_day_trader.stop()
            self.day_trading_process.terminate()
        except Exception:
            traceback.print_exc()

        try:
            # Stop swing trading process.
            self.live_swing_trader.stop()
            self.swing_trading_process.terminate()
        except Exception:
            traceback.print_exc()

        self.info_main('Shutdown complete')
