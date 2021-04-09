from datetime import datetime
from typing import List, Dict

from tc2.util.date_util import DATE_TIME_FORMAT


class StrategySymbolRun:
    """
    Wrapper holding data on how a symbol was traded during the course of strategy execution.
    """

    # The symbol that was traded (or not traded, if all the below lists are empty).
    symbol: str
    # The moments when the symbol was bought.
    times_bought: List[datetime]
    # The moments when the symbol was sold.
    times_sold: List[datetime]
    # The number of shares bought/sold in each trade.
    qties_traded: List[int]
    # The prices at which the symbol was bought.
    buy_prices: List[float]
    # The prices at which the symbol was sold.
    sell_prices: List[float]

    def __init__(self,
                 symbol: str,
                 times_bought: List[datetime],
                 times_sold: List[datetime],
                 qties_traded: List[int],
                 buy_prices: List[float],
                 sell_prices: List[float]) -> None:
        self.symbol = symbol
        self.times_bought = times_bought
        self.times_sold = times_sold
        self.qties_traded = qties_traded
        self.buy_prices = buy_prices
        self.sell_prices = sell_prices

    def to_json(self) -> Dict:
        return {
            'symbol': self.symbol,
            'times_bought': [moment.strftime(DATE_TIME_FORMAT) for moment in self.times_bought],
            'times_sold': [moment.strftime(DATE_TIME_FORMAT) for moment in self.times_sold],
            'qties_traded': self.qties_traded,
            'buy_prices': self.buy_prices,
            'sell_prices': self.sell_prices
        }

    @classmethod
    def from_json(cls, data: Dict) -> 'StrategySymbolRun':
        return StrategySymbolRun(
            symbol=data['symbol'],
            times_bought=[datetime.strptime(moment_str, DATE_TIME_FORMAT) for moment_str in data['times_bought']],
            times_sold=[datetime.strptime(moment_str, DATE_TIME_FORMAT) for moment_str in data['times_sold']],
            qties_traded=data['qties_traded'],
            buy_prices=data['buy_prices'],
            sell_prices=data['sell_prices'])
