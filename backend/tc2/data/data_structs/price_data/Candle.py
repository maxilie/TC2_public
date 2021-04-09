import traceback
from datetime import datetime
from typing import Optional, Dict

from tc2.util.data_constants import DATA_SPLITTERS
from tc2.util.date_util import DATE_TIME_FORMAT


class Candle:
    """
    Represents a candle at second resolution.
    Contains the second's datetime, volume, open price, high price, low price, and close price.
    """
    moment: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    COMP_SPLITTER = DATA_SPLITTERS['level_2']

    def __init__(self, moment: datetime, open: float, high: float, low: float, close: float, volume: int) -> None:
        self.moment = moment
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def is_same(self, o: object) -> bool:
        return isinstance(o, Candle) and \
               self.__str__() == o.__str__()

    def __str__(self) -> str:
        return self.COMP_SPLITTER.join([self.moment.strftime(DATE_TIME_FORMAT), str(self.open), str(self.high),
                                        str(self.low), str(self.close), str(self.volume)])

    @staticmethod
    def from_str(candle_str: str) -> 'Candle':
        moment: Optional[datetime] = None
        open: Optional[float] = None
        high: Optional[float] = None
        low: Optional[float] = None
        close: Optional[float] = None
        volume: Optional[int] = None
        for j, candle_comp in enumerate(candle_str.split(Candle.COMP_SPLITTER)):
            if j == 0:
                moment = datetime.strptime(candle_comp, DATE_TIME_FORMAT)
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
        return Candle(moment, open, high, low, close, volume)

    @classmethod
    def from_json(cls, data: Dict[str, str]) -> Optional['Candle']:
        """Converts the json dictionary to a Candle object."""
        try:
            return Candle(moment=datetime.strptime(data['moment'], DATE_TIME_FORMAT),
                          open=float(data['open']),
                          high=float(data['high']),
                          low=float(data['low']),
                          close=float(data['close']),
                          volume=int(data['volume']))
        except Exception as e:
            traceback.print_exc()
            return None

    def to_json(self) -> Dict[str, any]:
        """Converts the Candle to a json dictionary that can be read by javascript visualization functions."""
        return {
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'moment': self.moment.strftime(DATE_TIME_FORMAT)
        }
