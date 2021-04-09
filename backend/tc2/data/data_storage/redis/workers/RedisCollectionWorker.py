from datetime import date

from tc2.data.data_storage.redis.workers.AbstractRedisWorker import AbstractRedisWorker
from tc2.util.date_util import DATE_FORMAT


class RedisCollectionWorker(AbstractRedisWorker):
    """
    Contains functionality for tracking metadata on collection of stock market data.
    """

    def get_day_difficulty(self,
                           symbol: str,
                           day_date: date) -> int:
        """
        Returns the number of failed attempts at collecting data for symbol on day_date.
        """
        difficulty_str = self.client.hget(self.get_prefix() + 'COLLECTION-DATA',
                                          f'{symbol}_{day_date.strftime(DATE_FORMAT)}')
        difficulty_str = '' if difficulty_str is None else difficulty_str.decode("utf-8")
        return int(difficulty_str) if len(difficulty_str) != 0 else 0

    def incr_day_difficulty(self,
                            symbol: str,
                            day_date: date) -> None:
        """
        Increments the number of failed attempts at collecting data for symbol on day_date.
        """
        self.client.hset(self.get_prefix() + 'COLLECTION-DATA',
                         f'{symbol}_{day_date.strftime(DATE_FORMAT)}',
                         f'{self.get_day_difficulty(symbol, day_date) + 1}')

    def reset_day_difficulty(self,
                             symbol: str,
                             day_date: date) -> None:
        """
        Removes data on failed data collection attempts for symbol on day_date.
        """
        self.client.hdel(self.get_prefix() + 'COLLECTION-DATA',
                         f'{symbol}_{day_date.strftime(DATE_FORMAT)}')

    def reset_day_difficulties(self) -> None:
        """
        Removes data on failed data collection attempts for all symbols and dates.
        """
        self.client.delete(self.get_prefix() + 'COLLECTION-DATA')
