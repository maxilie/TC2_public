import json
from typing import Dict, Optional


class Position:
    """
    A position held in a symbol, defined by its symbol and number of shares.
    """
    symbol: str
    shares: int

    def __init__(self, symbol: str, shares: int) -> None:
        self.symbol = symbol
        self.shares = shares

    def get_symbol(self) -> str:
        return self.symbol

    def get_shares(self) -> int:
        return self.shares

    @staticmethod
    def from_str(data_str: str) -> 'Position':
        return Position.from_json(json.loads(data_str))

    def __str__(self) -> str:
        return json.dumps(self.to_json())

    def to_json(self) -> Dict[str, any]:
        return {
            'symbol': self.symbol,
            'shares': self.shares,
        }

    @staticmethod
    def from_json(data: Dict[str, any]) -> Optional['Position']:
        try:
            return Position(symbol=data['symbol'],
                            shares=int(data['shares']))
        except Exception as e:
            return None
