import traceback
from datetime import date, datetime
from typing import Optional, Dict

from tc2.data.data_structs.price_data.Candle import Candle
from tc2.util.data_constants import DATA_SPLITTERS
from tc2.util.date_util import DATE_FORMAT


class DailyCandle:
    """
    Represents a candle at daily resolution.
    Contains the days's date, volume, open price, high price, low price, and close price.
    """
    day_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int

    COMP_SPLITTER = DATA_SPLITTERS['level_2']

    def __init__(self, day_date: date, open: float, high: float, low: float, close: float, volume: int) -> None:
        self.day_date = day_date
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def is_same(self, o: object) -> bool:
        return isinstance(o, DailyCandle) and \
               self.__str__() == o.__str__()

    def __str__(self) -> str:
        return self.COMP_SPLITTER.join([self.day_date.strftime(DATE_FORMAT), str(self.open), str(self.high),
                                        str(self.low), str(self.close), str(self.volume)])

    @staticmethod
    def from_str(candle_str: str) -> 'DailyCandle':
        day_date: Optional[date] = None
        open: Optional[float] = None
        high: Optional[float] = None
        low: Optional[float] = None
        close: Optional[float] = None
        volume: Optional[int] = None
        for j, candle_comp in enumerate(candle_str.split(Candle.COMP_SPLITTER)):
            if j == 0:
                day_date = datetime.strptime(candle_comp, DATE_FORMAT)
            elif j == 1:
                open = float(candle_comp)
            elif j == 2:
                high = float(candle_comp)
            elif j == 3:
                low = float(candle_comp)
            elif j == 4:
                close = float(candle_comp)
            elif j == 5:
                volume = int(candle_comp)
        return DailyCandle(day_date, open, high, low, close, volume)

    @staticmethod
    def from_json(data: Dict[str, str]) -> Optional['DailyCandle']:
        """Converts the json dictionary to a DailyCandle object."""
        try:
            return DailyCandle(day_date=datetime.strptime(data['day_date'], DATE_FORMAT),
                               open=float(data['open']),
                               high=float(data['high']),
                               low=float(data['low']),
                               close=float(data['close']),
                               volume=int(data['volume']))
        except Exception as e:
            traceback.print_exc()
            return None

    def to_json(self):
        return {
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'day_date': self.day_date.strftime(DATE_FORMAT)
        }
