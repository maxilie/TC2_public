from datetime import date
from typing import Optional

from tc2.env.TimeEnv import TimeEnv
from tc2.log.LogFeed import LogFeed
from tc2.log.Loggable import Loggable
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay

POLYGON_DATE_FORMAT = '%Y-%m-%d'


class AbstractDataCollector(Loggable):
    """Provides access to a provider of stock market data."""
    time_env: TimeEnv

    def __init__(self, logfeed_program: LogFeed, logfeed_process: LogFeed, time_env: TimeEnv) -> None:
        super().__init__(logfeed_program, logfeed_process)

        self.time_env = time_env

    def collect_candles_for_day(self, day: date, symbol: str) -> Optional[SymbolDay]:
        """Collects candles for the symbol on the day."""
        raise NotImplementedError
