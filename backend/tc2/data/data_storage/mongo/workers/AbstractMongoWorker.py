from pymongo import collection

from tc2.env.EnvType import EnvType
from tc2.log.LogFeed import LogFeed
from tc2.log.Loggable import Loggable


class AbstractMongoWorker(Loggable):
    """A class equipped with access to MongoDB collections; used to perform a group of specific tasks."""

    candle_collection_secondly: collection
    candle_collection_daily: collection
    neural_collection: collection
    env_type: EnvType

    def __init__(self, logfeed_program: LogFeed,
                 candle_collection_secondly: collection,
                 candle_collection_daily: collection,
                 neural_collection: collection,
                 env_type: EnvType):
        # Route all logs to the main LogFeed
        super().__init__(logfeed_program=logfeed_program, logfeed_process=logfeed_program)

        self.candle_collection_secondly = candle_collection_secondly
        self.candle_collection_daily = candle_collection_daily
        self.neural_collection = neural_collection
        self.env_type = env_type
