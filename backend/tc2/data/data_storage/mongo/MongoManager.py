import os
import traceback
from datetime import date
from typing import Optional, List

import pymongo

from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.data.data_structs.neural_data.NeuralExample import NeuralExample
from tc2.data.data_structs.price_data.DailyCandle import DailyCandle
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.env.EnvType import EnvType
from tc2.log.LogFeed import LogFeed
from tc2.log.Loggable import Loggable
from tc2.data.data_storage.mongo.workers.MongoNeuralWorker import MongoNeuralWorker
from tc2.data.data_storage.mongo.workers.MongoPriceWorker import MongoPriceWorker
from tc2.util.synchronization import synchronized_on_mongo


class MongoManager(Loggable):
    client: pymongo.MongoClient
    env_type: EnvType
    _connected: bool
    _pid: int

    # Workers
    price_worker: MongoPriceWorker
    neural_worker: MongoNeuralWorker

    def __init__(self,
                 logfeed_program: LogFeed,
                 env_type: EnvType) -> None:
        # Route all logs to the program's LogFeed (all minor messages should be displayed in debug_output)
        super().__init__(logfeed_program=logfeed_program, logfeed_process=logfeed_program)

        # Set environment
        self.env_type = env_type
        self._connected = False
        self._pid = os.getpid()

    def connect(self,
                user: str,
                password: str,
                ip: str,
                port: str) -> bool:
        """Return false if there was a problem initializing the connection."""
        try:
            self.client = pymongo.MongoClient(
                f'mongodb://{user}:{password}@{ip}:{port}')

            # Test accessing a document collection
            # noinspection PyTypeChecker
            self.db = self.client["stocks_" + self.env_type.value]
            self.candle_collection_secondly = self.db["candle_dates_secondly"]
            self.candle_collection_daily = self.db["candle_dates_daily"]
            self.neural_collection = self.db["ai_datetimes"]
            self.candle_collection_secondly.find_one({"symbol": 'TEST', "date": 'TEST'})

            # Create workers
            self.price_worker = MongoPriceWorker(logfeed_program=self.logfeed_program,
                                                 candle_collection_secondly=self.candle_collection_secondly,
                                                 candle_collection_daily=self.candle_collection_daily,
                                                 neural_collection=self.neural_collection,
                                                 env_type=self.env_type)
            self.neural_worker = MongoNeuralWorker(logfeed_program=self.logfeed_program,
                                                   candle_collection_secondly=self.candle_collection_secondly,
                                                   candle_collection_daily=self.candle_collection_daily,
                                                   neural_collection=self.neural_collection,
                                                   env_type=self.env_type)

            self._connected = True
        except Exception:
            self.error_main(f'Could not initialize connection to MongoDB in #{self._pid}:')
            self.warn_main(traceback.format_exc())
            return False
        return True

    """
    Raw stock market price + volume data storage...
    """

    @synchronized_on_mongo
    def get_dates_on_file(self,
                          symbol: str,
                          start_date: date,
                          end_date: date,
                          debug_output: Optional[List[str]] = None) -> List[date]:
        return self.price_worker.get_dates_on_file(symbol, start_date, end_date, debug_output)

    @synchronized_on_mongo
    def load_symbol_day(self,
                        symbol: str,
                        day: date,
                        debug_output: Optional[List[str]] = None) -> SymbolDay:
        return self.price_worker.load_symbol_day(symbol, day, debug_output)

    @synchronized_on_mongo
    def load_aggregate_candle(self,
                              symbol: str,
                              day: date,
                              debug_output: Optional[List[str]]) -> Optional[DailyCandle]:
        return self.price_worker.load_aggregate_candle(symbol, day, debug_output)

    @synchronized_on_mongo
    def save_symbol_day(self,
                        day_data: SymbolDay,
                        debug_output: Optional[List[str]] = None) -> None:
        return self.price_worker.save_symbol_day(day_data, debug_output)

    def remove_price_data_before(self,
                                 symbol: str,
                                 cutoff_date: date,
                                 debug_output: Optional[List[str]] = None) -> None:
        return self.price_worker.remove_price_data_before(symbol, cutoff_date, debug_output)

    def remove_price_data_after(self,
                                symbol: str,
                                cutoff_date: date,
                                today: date,
                                debug_output: Optional[List[str]] = None) -> None:
        return self.price_worker.remove_price_data_after(symbol, cutoff_date, today, debug_output)

    @synchronized_on_mongo
    def drop_symbol(self,
                    symbol: str) -> None:
        return self.price_worker.drop_symbol(symbol)

    """
    Neural network training data storage...
    """

    @synchronized_on_mongo
    def load_example_collection(self,
                                symbol: str,
                                model_type: AnalysisModelType) -> List[NeuralExample]:
        return self.neural_worker.load_example_collection(symbol, model_type)

    @synchronized_on_mongo
    def save_neural_collection(self,
                               symbol: str,
                               model_type: AnalysisModelType,
                               examples: List[NeuralExample]) -> None:
        return self.neural_worker.save_neural_collection(symbol, model_type, examples)

    @synchronized_on_mongo
    def drop_neural_collection(self,
                               symbol: Optional[str],
                               model_type: AnalysisModelType) -> None:
        return self.neural_worker.drop_neural_collection(symbol, model_type)

    """
    Method to completely wipe the database...
    """

    def clear_db(self) -> None:
        """Removes all candle data and analysis/ai data from MongoDB."""
        self.candle_collection_secondly.delete_many({})
        self.candle_collection_daily.delete_many({})
        self.neural_collection.delete_many({})
        if self.env_type is EnvType.LIVE:
            self.error_main(f'Cleared all candles from LIVE environment')

    def shutdown(self) -> None:
        try:
            self.client.close()
        except Exception:
            traceback.print_exc()
