import traceback
from datetime import date, datetime
from typing import Optional, Dict

from tc2.data.data_structs.price_data.Candle import Candle
from tc2.util.data_constants import DATA_SPLITTERS
from tc2.util.date_util import DATE_TIME_FORMAT


class MinuteCandle:
    """
    Represents a candle at minute resolution.
    Contains the candle's minute, volume, open price, high price, low price, and close price.
    """
    minute: date
    open: float
    high: float
    low: float
    close: float
    volume: int

    COMP_SPLITTER = DATA_SPLITTERS['level_2']

    def __init__(self, minute: datetime, open: float, high: float, low: float, close: float, volume: int) -> None:
        self.minute = minute
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def is_same(self, o: object) -> bool:
        return isinstance(o, MinuteCandle) and \
               self.__str__() == o.__str__()

    def __str__(self) -> str:
        return self.COMP_SPLITTER.join([self.minute.strftime(DATE_TIME_FORMAT), str(self.open), str(self.high),
                                        str(self.low), str(self.close), str(self.volume)])

    @staticmethod
    def from_str(candle_str: str) -> 'MinuteCandle':
        minute: Optional[datetime] = None
        open: Optional[float] = None
        high: Optional[float] = None
        low: Optional[float] = None
        close: Optional[float] = None
        volume: Optional[int] = None
        for j, candle_comp in enumerate(candle_str.split(Candle.COMP_SPLITTER)):
            if j == 0:
                minute = datetime.strptime(candle_comp, DATE_TIME_FORMAT)
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
        return MinuteCandle(minute, open, high, low, close, volume)

    @staticmethod
    def from_json(data: Dict[str, str]) -> Optional['MinuteCandle']:
        """Converts the json dictionary to a MinuteCandle object."""
        try:
            return MinuteCandle(minute=datetime.strptime(data['minute'], DATE_TIME_FORMAT),
                                open=float(data['open']),
                                high=float(data['high']),
                                low=float(data['low']),
                                close=float(data['close']),
                                volume=int(data['volume']))
        except Exception as e:
            traceback.print_exc()
            return None

    def to_json(self):
        """Converts the MinuteCandle to a json dictionary that can be read by javascript visualization functions."""
        return {
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'minute': self.minute.strftime(DATE_TIME_FORMAT)
        }
