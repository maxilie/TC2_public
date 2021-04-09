from datetime import datetime
from typing import Dict, Optional

from tc2.util.data_constants import DATA_SPLITTERS
from tc2.util.date_util import DATE_TIME_FORMAT


class RoundTripTrade:
    """A pairing of a filled buy order with its corresponding filled sell order on the same day."""
    symbol: str
    buy_time: datetime
    sell_time: datetime
    buy_price: float
    sell_price: float
    qty: int

    def __init__(self, symbol: str, buy_time: datetime, sell_time: datetime, buy_price: float, sell_price: float,
                 qty: int) -> None:
        self.symbol = symbol
        self.buy_time = buy_time
        self.sell_time = sell_time
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.qty = qty

    @classmethod
    def from_string(cls, data_str: str) -> 'RoundTripTrade':
        data = data_str.split(DATA_SPLITTERS['level_1'])
        return cls(data[0],
                   datetime.strptime(data[1], DATE_TIME_FORMAT),
                   datetime.strptime(data[2], DATE_TIME_FORMAT),
                   float(data[3]),
                   float(data[4]),
                   int(data[5]))

    def get_symbol(self) -> str:
        return self.symbol

    def get_buy_time(self) -> datetime:
        return self.buy_time

    def get_sell_time(self) -> datetime:
        return self.sell_time

    def get_buy_price(self) -> float:
        return self.buy_price

    def get_sell_price(self) -> float:
        return self.sell_price

    def get_qty(self) -> int:
        return self.qty

    def __str__(self) -> str:
        return DATA_SPLITTERS['level_1'].join([self.get_symbols()[0],
                                               datetime.strftime(self.get_buy_time(), DATE_TIME_FORMAT),
                                               datetime.strftime(self.get_sell_time(), DATE_TIME_FORMAT),
                                               str(self.get_buy_price()),
                                               str(self.get_sell_price()),
                                               str(self.get_qty())])

    def to_json(self) -> Dict[str, any]:
        return {
            'symbol': self.symbol,
            'buy_time': self.buy_time.strftime(DATE_TIME_FORMAT),
            'sell_time': self.sell_time.strftime(DATE_TIME_FORMAT),
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'qty': self.qty
        }

    @staticmethod
    def from_json(cls, data: Dict[str, any]) -> Optional['RoundTripTrade']:
        try:
            return RoundTripTrade(symbol=data['id'],
                                  buy_time=datetime.strptime(data['buy_time'], DATE_TIME_FORMAT),
                                  sell_time=datetime.strptime(data['sell_time'], DATE_TIME_FORMAT),
                                  buy_price=float(data['buy_price']),
                                  sell_price=float(data['sell_price']),
                                  qty=int(data['qty']), )
        except Exception as e:
            return None
