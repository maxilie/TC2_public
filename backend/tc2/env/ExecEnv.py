import multiprocessing
import os
import traceback
from datetime import datetime, timedelta
from typing import List, Optional

from tc2.data.data_storage.mongo.MongoManager import MongoManager
from tc2.data.data_storage.redis.RedisManager import RedisManager
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.data.stock_data_collection.AbstractDataCollector import AbstractDataCollector
from tc2.env.EnvType import EnvType
from tc2.env.TimeEnv import TimeEnv
from tc2.log.LogFeed import LogFeed
from tc2.log.Loggable import Loggable
from tc2.util.market_util import CLOSE_TIME


class ExecEnv(Loggable):
    """
    Mediates sharing and separation of data and time environments (live vs simulated) across multiple threads/processes.
    Every thread/process has its own ExecEnv for each EnvType it uses.
    One thread/process can access the mongo data of another by forking it's ExecEnv.
    """

    # The type of this execution environment.
    env_type: EnvType

    # Program settings - one instance shared across threads and ExecEnv's, even of different EnvType.
    _settings: 'multiprocessing dict'

    # Time environment - identical clones shared across threads running the same EnvType.
    _time: TimeEnv

    # Data collector - identical clones shared across threads running the same EnvType.
    _data_collector: AbstractDataCollector

    # Data load status - one instance shared across threads running the same EnvType.
    _data_loaded: 'multiprocessing dict'

    # MongoDB manager - specific to this (thread, ExecEnv) pair.
    _mongo: MongoManager

    # Redis manager - specific to this (thread, ExecEnv) pair.
    _redis: RedisManager

    # The process id of this thread.
    _pid: int

    # List shared across threads to ensure each EnvType is created from scratch only once.
    instantiated_env_types: 'multiprocessing list' = None

    """
    Time accessor...
    """

    def time(self) -> TimeEnv:
        """Provides access to the environment's time variables and methods."""
        return self._time

    """
    Database accessors...
    """

    def mongo(self) -> MongoManager:
        """Provides access to MongoDB while ensuring calls are made from only one thread."""
        if os.getpid() != self._pid:
            raise EnvironmentError(f'Thread with pid {os.getpid()} tried to access MongoDB '
                                   f'for thread with pid {self._pid}')
        return self._mongo

    def redis(self) -> RedisManager:
        """Provides access to Redis while ensuring calls are made from only one thread."""
        if os.getpid() != self._pid:
            raise EnvironmentError(f'Thread with pid {os.getpid()} tried to access Redis '
                                   f'for thread with pid {self._pid}')
        return self._redis

    """
    Settings getter & setter...
    """

    def get_setting(self, setting_name: str) -> str:
        """Returns a setting value as a raw string."""
        return self._settings[setting_name.lower()] if setting_name.lower() in self._settings else ''

    def save_setting(self, setting_name: str, setting_val: str) -> None:
        """Saves the setting to Redis, which will cause it to persist even if the config.properties file is reset."""
        self._settings[setting_name.lower()] = setting_val
        self.redis().set_setting(setting_name.lower(), setting_val)

    """
    DataCollector accessor...
    """

    def data_collector(self) -> AbstractDataCollector:
        """Provides access to the environment's data collection functionalities."""
        return self._data_collector

    """
    Data load marking methods...
    """

    def is_data_loaded(self) -> bool:
        """Returns True only if a thread on this EnvType has called mark_data_as_loaded()."""
        return self._data_loaded[self.env_type.value]

    def mark_data_as_loaded(self) -> None:
        """Marks data as loaded for all ExecEnv's of the same EnvType (even across different threads)."""
        self._data_loaded[self.env_type.value] = True

    def mark_data_as_busy(self) -> None:
        """Marks data as busy for all ExecEnv's of this EnvType (even across different threads)."""
        self._data_loaded[self.env_type.value] = False

    """
    Data fetching methods...
    """

    def get_latest_candles(self, symbol: str, minutes: float) -> List[Candle]:
        """
        Combines today's cached redis candles with historical candles from MongoDB.
        NOTE: if current time is 10:32:54, minutes=32 means "fetch candles starting at 10:00:00"

       :param minutes: minutes of open market data to fetch, NOT total minutes including closing hours
       """

        # Calculate the furthest back we should go in time
        start_moment: datetime = self.time().now().replace(microsecond=0)
        mins_accounted_for = 0
        while mins_accounted_for < minutes:
            # Go back minute-by-minute
            start_moment = start_moment - timedelta(minutes=1)

            # When market close is reached, go back to the previous market day
            if not self.time().is_open(start_moment):
                start_moment = datetime.combine(self.time().get_prev_mkt_day(start_moment.date()),
                                                CLOSE_TIME.replace(second=start_moment.second)) - timedelta(minutes=1)

            mins_accounted_for += 1

        # Fetch candles by working backward from now
        candles = []
        day_date = self.time().get_next_mkt_day()
        while day_date >= start_moment.date():
            day_date = self.time().get_prev_mkt_day(day_date)
            if day_date == self.time().now().date() and self.env_type is EnvType.LIVE:
                # Fetch today's candles from redis cache
                cached_candles = self.redis().get_cached_candles(symbol, day_date)
                # Use candles that fall within the desired time interval
                cached_candles.sort(key=lambda candle_to_sort: candle_to_sort.moment, reverse=True)
                for candle in cached_candles:
                    if start_moment - timedelta(milliseconds=1) <= candle.moment <= self.time().now():
                        candles.append(candle)
            else:
                # Fetch previous days' candles from MongoDB
                mongo_candles = self.mongo().load_symbol_day(symbol, day_date).candles
                # Use candles that fall within the desired time interval
                for candle in mongo_candles:
                    if start_moment - timedelta(milliseconds=1) <= candle.moment <= self.time().now():
                        candles.append(candle)

        # Sort candles into ascending order
        candles.sort(key=lambda candle_to_sort: candle_to_sort.moment)
        return candles

    """
    Init methods...
    """

    def __init__(self, logfeed_program: LogFeed,
                 logfeed_process: LogFeed,
                 creator_env: Optional['ExecEnv'] = None):
        super().__init__(logfeed_program, logfeed_process)
        self._creator_env = creator_env

    def setup_first_time(self, env_type: EnvType,
                         time: TimeEnv,
                         data_collector: AbstractDataCollector,
                         mongo: MongoManager,
                         redis: RedisManager) -> None:
        """
        Initializes database connections and marks data as not loaded.
        """

        # Ensure this is called only once per EnvType
        if ExecEnv.instantiated_env_types is None:
            ExecEnv.instantiated_env_types = multiprocessing.Manager().list()
        if env_type.name in ExecEnv.instantiated_env_types:
            raise Exception(f'Tried to setup {env_type.name} ExecEnv twice')
        else:
            ExecEnv.instantiated_env_types.append(env_type.name)

        # Init the environment's variables
        self.env_type = env_type
        self._time = time
        self._data_collector = data_collector
        try:
            if env_type.value not in self._data_loaded.keys():
                self._data_loaded[env_type.value] = False
        except AttributeError as e:
            self._data_loaded = multiprocessing.Manager().dict()
            if env_type.value not in self._data_loaded.keys():
                self._data_loaded[env_type.value] = False
        self._mongo = mongo
        self._redis = redis
        self._settings = multiprocessing.Manager().dict()
        self._pid = os.getpid()

        # Validate environment types of this environment and its database managers
        if env_type != mongo.env_type != redis.env_type:
            self.error_main('COULD NOT SETUP EXECUTION ENVIRONMENT! '
                            'EnvType of the ExecEnv must match that of its mongo and redis managers...')

        # Load settings and use them to init db connections
        try:
            self._load_settings_from_config()
            self._init_db_connections()
            self._load_settings_from_redis()
        except Exception as e:
            self.error_main('ExecEnv could not load settings and connect to the databases:')
            self.warn_main(traceback.format_exc())

    def clone_same_thread(self, creator_env: Optional['ExecEnv'] = None) -> None:
        """
        Copies creator_env's variables into this ExecEnv.
        """
        if creator_env is None and self._creator_env is None:
            raise ValueError('Can\'t clone an execution environment on the same thread without a creator env')
        elif creator_env is None:
            creator_env = self._creator_env

        # Ensure this ExecEnv and creator_env are on the same thread
        if os.getpid() != creator_env._pid:
            raise EnvironmentError(f'Tried to clone thread #{creator_env._pid}\'s ExecEnv variables in '
                                   f'thread #{os.getpid()}. Use self.fork_new_thread() instead.')
        self.env_type = creator_env.env_type
        self._time = creator_env._time
        self._data_collector = creator_env._data_collector
        self._mongo = creator_env._mongo
        self._redis = creator_env._redis
        self._pid = creator_env._pid
        self._settings = creator_env._settings
        self._data_loaded = creator_env._data_loaded

    def fork_new_thread(self, creator_env: Optional['ExecEnv'] = None) -> None:
        """
        Copies over creator_env's settings and creates new database accessors for this thread.
        """
        if creator_env is None and self._creator_env is None:
            raise ValueError('Can\'t clone an execution environment on the same thread without a creator env')
        elif creator_env is None:
            creator_env = self._creator_env

        self.env_type = creator_env.env_type
        self._time = creator_env._time
        self._data_collector = creator_env._data_collector
        self._data_loaded = creator_env._data_loaded
        self._pid = os.getpid()

        # Create new database accessors for the new thread
        self._mongo = MongoManager(logfeed_program=self.logfeed_program,
                                   env_type=self.env_type)
        self._redis = RedisManager(logfeed_process=self.logfeed_process,
                                   env_type=self.env_type)

        # Load settings and use them to init db connections
        try:
            self._load_settings_from_config()
            self._init_db_connections()
            self._load_settings_from_redis()
        except Exception as e:
            self.error_main('ExecEnv could not load settings and connect to databases:')
            self.warn_main(traceback.format_exc())

    """
    Private init methods...
    """

    def _load_settings_from_config(self) -> None:
        """
        Parses the config file and loads its settings into memory.
        These should only include static settings (database credentials).
        """
        try:
            file = open("config.properties")
            lines = file.readlines()
            self._settings = {}
            for line in lines:
                if line.startswith("#") or len(line.strip()) == 0:
                    continue
                comps = line.split("=")
                if len(comps) < 2:
                    print("INVALID CONFIG LINE: '" + line + "'")
                    continue
                key = line.split("=")[0].strip().lower()
                val = ''.join(line.split("=")[1:]).strip()
                self._settings[key] = val
        except Exception as e:
            self.error_process('Error loading settings from config file:')
            self.warn_process(traceback.format_exc())

    def _init_db_connections(self) -> None:
        if not self._mongo.connect(
                user=self.get_setting('mongo.user'),
                password=self.get_setting('mongo.pass'),
                ip=self.get_setting('mongo.ip'),
                port=self.get_setting('mongo.port')):
            self.error_main(f'{self.env_type.name} environment could not initialize connection to MongoDB database')

        if not self._redis.connect(
                ip=self.get_setting('redis.ip'),
                port=self.get_setting('redis.port')):
            self.error_main(f'{self.env_type.name} environment could not initialize connection to MongoDB database')

    def _load_settings_from_redis(self) -> None:
        """
        Overwrites any config-file settings with settings saved in Redis.
        """
        try:
            setting_keys = [
                'symbols',
                'alpaca.endpoint'
            ]
            for setting_key in setting_keys:
                setting_str = self.redis().get_setting(setting_key)
                if setting_str is not None:
                    self._settings[setting_key] = setting_str
                self.redis().set_setting(setting_key, self._settings[setting_key])

        except Exception as e:
            self.error_process('Error loading settings from Redis:')
            self.warn_process(traceback.format_exc())

    """
    Reset method...
    """

    def reset_dbs(self) -> None:
        """
        Clears MongoDB and Redis databases of all data stored under this EnvType.
        """
        self.mongo().clear_db()
        self.redis().clear_db()
