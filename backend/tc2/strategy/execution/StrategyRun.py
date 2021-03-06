import json
import traceback
from datetime import datetime
from typing import Optional, Dict, List

from tc2.strategy.execution.StrategySymbolRun import StrategySymbolRun
from tc2.util.date_util import DATE_TIME_FORMAT


class RunMetadata:
    """Can be extended to include any run info specific to a strategy."""

    _data: Dict[str, str]

    def __init__(self, data: Dict[str, str]) -> None:
        """Handles the module (file) name and class name so we can serialize the class."""
        self._data = data

    def get_float(self, fieldname: str) -> float:
        """Returns the data stored under the given fieldname."""
        return float(self._data[fieldname])

    def get_str(self, fieldname: str) -> str:
        """Returns the data stored under the given fieldname."""
        return str(self._data[fieldname])

    @classmethod
    def from_string(cls, data_str: str) -> 'RunMetadata':
        """Deserializes the metadata object from a string."""
        data_dict = json.loads(data_str)
        return RunMetadata(data_dict)

    def __str__(self) -> str:
        """Serializes the metadata object into a string."""
        return json.dumps(self._data)


class StrategyRun:
    """
    Generated by a strategy after it has run its course.
    Contains info on the course of a strategy's execution.
    It doesn't matter whether the strategy was executed live or simulated historically.
    Any strategy that wants to record its own details can do so by attaching AbstractStrategyMetadata here.
    """

    # The symbol(s) being traded by the strategy
    symbol_runs: List[StrategySymbolRun]

    # The moment when execution of the strategy began
    strategy_start_time: datetime

    # The moment when execution of the strategy finished
    strategy_end_time: datetime

    # Optional metadata about the strategy run, specific to each strategy
    metadata: Optional[RunMetadata]

    def __init__(self,
                 symbol_runs: List[StrategySymbolRun],
                 strategy_start_time: datetime, strategy_end_time: datetime,
                 metadata: Optional[RunMetadata] = None) -> None:
        self.symbol_runs = symbol_runs
        self.strategy_start_time = strategy_start_time
        self.strategy_end_time = strategy_end_time
        self.metadata = metadata

    def record_purchase(self,
                        symbol: str,
                        price: float,
                        qty: int,
                        moment: datetime) -> None:
        """
        Logs a purchase made by a strategy into the strategy's run info.
        """

        # Search for an existing StrategySymbolRun to modify
        symbol_placed = False
        for symbol_run in self.symbol_runs:
            if symbol_run.symbol == symbol:
                symbol_placed = True
                symbol_run.buy_prices.append(price)
                symbol_run.times_bought.append(moment)
                symbol_run.qties_traded.append(qty)

        # If no StrategySymbolRun exists for the symbol, make a new one
        if not symbol_placed:
            self.symbol_runs.append(StrategySymbolRun(symbol=symbol,
                                                      times_bought=[moment],
                                                      times_sold=[],
                                                      qties_traded=[qty],
                                                      buy_prices=[price],
                                                      sell_prices=[]))

    def record_sale(self,
                    symbol: str,
                    price: float,
                    qty: int,
                    moment: datetime) -> None:
        """
        Logs a sale made by a strategy into the strategy's run info.
        """

        # Search for an existing StrategySymbolRun to modify
        symbol_placed = False
        for symbol_run in self.symbol_runs:
            if symbol_run.symbol == symbol:
                symbol_placed = True
                symbol_run.sell_prices.append(price)
                symbol_run.times_sold.append(moment)

        # If no StrategySymbolRun exists for the symbol, make a new one
        if not symbol_placed:
            self.symbol_runs.append(StrategySymbolRun(symbol=symbol,
                                                      times_bought=[],
                                                      times_sold=[moment],
                                                      qties_traded=[qty],
                                                      buy_prices=[],
                                                      sell_prices=[price]))

    @classmethod
    def from_string(cls, data_str: str) -> 'StrategyRun':
        """Decodes and returns a StrategyRun object that has been serialized into a string."""
        return StrategyRun.from_json(json.loads(data_str))

    def __str__(self) -> str:
        return json.dumps(self.to_json())

    def to_json(self) -> Dict:
        return {
            'symbol_runs': [symbol_run.to_json() for symbol_run in self.symbol_runs],
            'strategy_start_time': self.strategy_start_time.strftime(DATE_TIME_FORMAT),
            'strategy_end_time': self.strategy_end_time.strftime(
                DATE_TIME_FORMAT) if self.strategy_end_time is not None else '',
            'metadata': str(self.metadata) if self.metadata is not None else ''
        }

    @classmethod
    def from_json(cls, data: Dict) -> Optional['StrategyRun']:
        try:
            return StrategyRun(
                symbol_runs=[StrategySymbolRun.from_json(symbol_run_data) for symbol_run_data in data['symbol_runs']],
                strategy_start_time=datetime.strptime(data['strategy_start_time'], DATE_TIME_FORMAT),
                strategy_end_time=datetime.strptime(data['strategy_end_time'], DATE_TIME_FORMAT) \
                    if data['strategy_end_time'] != '' else None,
                metadata=RunMetadata.from_string(data['metadata']) if data['metadata'] != '' else None
            )
        except Exception as e:
            print('ERROR DECODING STRATEGY RUN:')
            traceback.print_exc()
            return None
