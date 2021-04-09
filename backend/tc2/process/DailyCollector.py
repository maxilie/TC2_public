import random
import time as pytime
import traceback
from datetime import timedelta, datetime, date

from tc2.account.AlpacaAccount import AlpacaAccount
from tc2.account.data_stream.StreamUpdateType import StreamUpdateType
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.data.stock_data_collection.ModelFeeder import ModelFeeder
from tc2.env.ExecEnv import ExecEnv
from tc2.env.Settings import Settings
from tc2.util.market_util import CLOSED_DURATION, MODEL_FEED_DELAY, OPEN_TIME, CLOSE_TIME


class DailyCollector(ExecEnv):
    """
    Logic loop that collects data and uses it to feed analysis models after markets close.
    """

    model_feeder: ModelFeeder

    def __init__(self, creator_env: ExecEnv, logfeed_process) -> None:
        super().__init__(creator_env.logfeed_program, logfeed_process=logfeed_process, creator_env=creator_env)

        self._running = False

    def start_collection_loop(self,
                              livestream_updates: 'multiprocessing list') -> None:
        """
        Continuously collects live data while markets are open.
        Collects polygon-rest data one hour after markets close.
        Trains analysis models on new data.
        """
        assert not self._running, 'Tried to start collection loop twice!'
        self._running = True

        # Fork the execution environment so it can run in this thread.
        self.fork_new_thread()

        # Create a ModelFeeder to train models.
        self.model_feeder = ModelFeeder(self)

        # Hook into polygon's live data stream.
        acct = AlpacaAccount(env=self, logfeed_trading=self.logfeed_process, livestream_updates=livestream_updates)

        # Wait for missing historical data to be collected at startup.
        while not self.is_data_loaded():
            pytime.sleep(1)

        # Calculate the next collection time.
        collection_time = self.next_collection_time(is_first_collection=True)

        # Start data collection loop.
        while self._running:

            # Wait 3 seconds between loops.
            pytime.sleep(3)

            # Cache live price data in redis.
            try:
                update = acct.get_next_trading_update(Settings.get_symbols(self))
                updates_processed = 0
                while update is not None:
                    if update.update_type is StreamUpdateType.CANDLE:
                        # self.info_process(f'Caching {update.raw_data["symbol"]} candle in redis')
                        self._cache_candle(symbol=update.raw_data['symbol'],
                                           candle=update.get_candle())
                    updates_processed += 1
                    update = acct.get_next_trading_update(Settings.get_symbols(self))
                if updates_processed > 500:
                    self.warn_process(f'DailyCollector processed {updates_processed} updates at once')
            except Exception as e:
                self.error_process('Error processing polygon live data:')
                self.warn_process(traceback.format_exc())

            # Collect data on all symbols and train analysis models.
            if self.time().now() > collection_time:
                self._collect_and_train()
                # Don't collect again until tomorrow.
                collection_time = self.next_collection_time(is_first_collection=False)

        # Display a message when the collection loop is stopped.
        self.info_process('DailyCollector collection loop stopped')

    def next_collection_time(self,
                             is_first_collection: bool) -> datetime:
        """
        Returns the number of seconds until 15 minutes after next market close time.

        :param is_first_collection: set to True to schedule collection immediately (if the markets are closed)
        """

        # If markets are closed and the program just started up, collect in a few seconds.
        if is_first_collection and not self.time().is_open() \
                and 0 < self.time().now().hour < 10 \
                and self.time().get_secs_to_open() < CLOSED_DURATION - MODEL_FEED_DELAY:
            return self.time().now() + timedelta(seconds=5)

        # Otherwise, collect 15 mins after the next market closing time.
        secs_to_close = self.time().get_secs_to_close() if self.time().is_open() \
            else self.time().get_secs_to_open() + timedelta(hours=6.5).total_seconds()
        return self.time().now() + timedelta(seconds=secs_to_close + MODEL_FEED_DELAY)

    def stop(self) -> None:
        """
        Cancels the collection task if it's queued, or terminates it if it's running.
        """
        self._running = False

    def _collect_and_train(self) -> None:
        """
        Collects polygon-rest data and trains analysis models on it.
        """
        self.info_process('\n\n')
        self.info_process('Performing daily data collection and model training...')

        for symbol in Settings.get_symbols(self):
            # Interrupt collection if the collection loop was stopped
            if not self._running:
                break

            # Revert data to last stable day.
            date_last_collected_for = self.time().now().date()
            # If it's past midnight, move back a day.
            if self.time().get_secs_to_open() < timedelta(hours=9, minutes=30).total_seconds():
                date_last_collected_for -= timedelta(days=1)
            # Move back two market days from the most recent market day.
            date_last_collected_for = self.time().get_prev_mkt_day(date_last_collected_for)
            date_last_collected_for = self.time().get_prev_mkt_day(date_last_collected_for)
            # Remove mongo price data after the stable day.
            self.mongo().remove_price_data_after(symbol, date_last_collected_for, today=self.time().now().today())
            date_rest_available_for = self.time().get_next_mkt_day(date_last_collected_for)

            # Collect yesterday's polygon-rest data and train on it.
            if self._train_on_rest_data(symbol, date_rest_available_for):
                self.info_process(f'Trained {symbol} on yesterday\'s polygon rest data')
            else:
                self.warn_process(f'Invalid {symbol} rest data collected for {date_rest_available_for}. '
                                  f'Discarding them and attempting to use cached stream data instead')
                if self._train_on_stream_data(symbol, date_rest_available_for):
                    self.info_process(f'Trained {symbol} on yesterday\'s polygon stream data')
                else:
                    self.warn_process(f'Invalid {symbol} candles cached for {date_rest_available_for}. '
                                      f'Could not find valid data to train on yesterday!')

            # Load today's polygon-stream data and train on it.
            date_cache_available_for = self.time().get_next_mkt_day(date_rest_available_for)
            if self._train_on_stream_data(symbol, date_cache_available_for):
                self.info_process(f'Trained {symbol} on today\'s polygon stream data')
            else:
                self.warn_process(f'Invalid {symbol} candles cached for {date_rest_available_for}. '
                                  f'Could not find valid data to train on today!')

    def _train_on_rest_data(self,
                            symbol: str,
                            day_date: date) -> bool:
        """
        Collects polygon-rest data and trains the symbol on it.
        Returns False if the collected data is invalid; True otherwise.
        """
        # Collect polygon-rest data
        rest_data = None
        try:
            rest_data = self.data_collector().collect_candles_for_day(day_date, symbol)
        except Exception as e:
            self.error_process('Error collecting polygon-rest data:')
            self.warn_process(traceback.format_exc())

        # Validate polygon-rest data
        if rest_data is None or not SymbolDay.validate_candles(rest_data.candles):
            self.redis().reset_day_difficulty(symbol, day_date)
            self.redis().incr_day_difficulty(symbol, day_date)
            return False

        # Save polygon-rest data
        self.redis().reset_day_difficulty(symbol, rest_data.day_date)
        self.mongo().save_symbol_day(rest_data)

        # Train models on polygon-rest data
        self.model_feeder.train_models(symbol=symbol,
                                       day_date=day_date,
                                       day_data=rest_data,
                                       stable=True)
        return True

    def _train_on_stream_data(self,
                              symbol: str,
                              day_date: date) -> bool:
        """
        Loads cached polygon-stream data and trains the symbol on it.
        Returns False if the data is invalid; True otherwise.
        """
        # Validate polygon-stream data
        stream_data = SymbolDay(
            symbol=symbol,
            day_date=day_date,
            candles=self.redis().get_cached_candles(
                symbol=symbol,
                day_date=day_date))
        if not SymbolDay.validate_candles(stream_data.candles):
            return False

        # Train models on polygon-stream data
        self.model_feeder.train_models(symbol=symbol,
                                       day_date=day_date,
                                       day_data=stream_data,
                                       stable=True)
        return True

    def _cache_candle(self,
                      symbol: str,
                      candle: Candle) -> None:
        """
        Stores a newly-streamed candle in redis cache.
        """
        # Cache the unstable candles so the program has access to recent data
        if datetime.combine(datetime.now().date(), OPEN_TIME) < candle.moment \
                < datetime.combine(datetime.now().date(), CLOSE_TIME):

            # Store unstable candle in redis cache
            self.redis().store_cached_candles(symbol=symbol,
                                              candles=[candle])

            # Occasionally prune unstable candles that are no longer needed
            if random.randint(0, 1000) < 3:
                self.redis().prune_cached_candles(symbol=symbol)
