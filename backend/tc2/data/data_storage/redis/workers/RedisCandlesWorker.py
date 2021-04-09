from datetime import date
from typing import List

from tc2.data.data_storage.redis.workers.AbstractRedisWorker import AbstractRedisWorker
from tc2.data.data_structs.price_data.Candle import Candle


class RedisCandlesWorker(AbstractRedisWorker):
    """
    Contains functionality for saving and loading candles in the cache.
    Long-term candle storage is handled by mongo.
    """

    def get_cached_candles(self, symbol: str, day_date: date) -> List[Candle]:
        """
        Gets candles cached from polygon stream.
        """

        # Get raw candle data from redis.
        candles_data = self.client.lrange(self.get_prefix() + 'STREAM-CANDLES_' + symbol, 0, -1)
        candles_data = [candle_str.decode("utf-8") for candle_str in candles_data]

        # Decode candles.
        if candles_data is None:
            return []
        candles = [Candle.from_str(candle_str) for candle_str in candles_data]
        candles.sort(key=lambda candle_to_sort: candle_to_sort.moment)

        # Filter out candles from other days.
        return [candle for candle in candles if candle.moment.date() == day_date]

    def prune_cached_candles(self, symbol: str, candles_to_keep: int = 50000) -> None:
        """
        :param symbol:
        :param candles_to_keep: keep this many of the latest candles (default is 2 days)
        """
        candles_on_file = self.client.llen(self.get_prefix() + 'STREAM-CANDLES_' + symbol)
        if candles_on_file > candles_to_keep:
            self.client.ltrim(self.get_prefix() + 'STREAM-CANDLES_' + symbol, candles_on_file - candles_to_keep, -1)

    def store_cached_candles(self, symbol: str, candles: List[Candle]) -> None:
        """
        Stores candles from polygon stream in redis.
        """
        self.client.rpush(self.get_prefix() + 'STREAM-CANDLES_' + symbol, *[str(candle) for candle in candles])
