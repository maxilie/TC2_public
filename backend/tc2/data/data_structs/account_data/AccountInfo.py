from typing import Dict, Optional

from tc2.util.data_constants import DATA_SPLITTERS


class AccountInfo:
    """The variables to be received in a json message from the brokerage."""
    id: str
    cash: float
    cash_withdrawable: float

    def __init__(self, id_str: str, cash: float, cash_withdrawable) -> None:
        self.id = id_str
        self.cash = cash
        self.cash_withdrawable = cash_withdrawable

    def __str__(self) -> str:
        return DATA_SPLITTERS['level_1'].join([self.id,
                                               str(self.cash),
                                               str(self.cash_withdrawable)])

    @staticmethod
    def from_string(data_str: str) -> 'AccountInfo':
        data = data_str.split(DATA_SPLITTERS['level_1'])
        return AccountInfo(id_str=data[0],
                           cash=float(data[1]),
                           cash_withdrawable=float(data[2]))

    def to_json(self) -> Dict[str, any]:
        return {
            'id': self.id,
            'cash': self.cash,
            'cash_withdrawable': self.cash_withdrawable
        }

    @classmethod
    def from_json(cls, data: Dict[str, any]) -> Optional['AccountInfo']:
        try:
            return AccountInfo(id_str=data['id'],
                               cash=float(data['cash']),
                               cash_withdrawable=float(data['cash_withdrawable']))
        except Exception as e:
            return None
