import traceback
import uuid
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from tc2.account.data_stream.StreamUpdateType import StreamUpdateType
from tc2.data.data_structs.account_data.AccountInfo import AccountInfo
from tc2.data.data_structs.account_data.Order import Order
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.util.date_util import DATE_TIME_FORMAT


class StreamUpdate:
    """
    An update from the broker or live data stream, meant to trigger strategy logic.
    """

    update_id: UUID
    update_moment: datetime
    update_type: StreamUpdateType
    raw_data: Dict[str, any]

    def __init__(self,
                 update_moment: datetime,
                 update_type: StreamUpdateType,
                 acct_info: dict = None,
                 symbol: str = None,
                 candle: dict = None,
                 order: dict = None):
        self.update_id = uuid.uuid4()
        self.update_moment = update_moment
        self.update_type = update_type
        self.raw_data = {
            'acct_info': acct_info,
            'symbol'   : symbol,
            'candle'   : candle,
            'order'    : order}

    def get_symbol(self) -> str:
        return self.raw_data['symbol']

    def get_candle(self) -> Candle:
        """
        Returns this update's candle.
        Only for StreamUpdateType.CANDLE.
        """
        return None if self.raw_data['candle'] is None else Candle.from_json(self.raw_data['candle'])

    def get_order(self) -> Optional[Order]:
        """
        Returns this update's order.
        Only for StreamUpdateType.ORDER.
        """
        return None if self.raw_data['order'] is None else Order.from_json(self.raw_data['order'])

    def get_acct_info(self) -> AccountInfo:
        """
        Returns this update's account info.
        Only for StreamUpdateType.ACCT_INFO.
        """
        return AccountInfo.from_json(self.raw_data['acct_info'])

    @classmethod
    def from_json(cls, json_data: Dict[str, any]) -> 'StreamUpdate':
        try:
            update = StreamUpdate(update_moment=datetime.strptime(json_data['update_moment'], DATE_TIME_FORMAT),
                                  update_type=StreamUpdateType[json_data['update_type']],
                                  **json_data['raw_data'])
            update.update_id = UUID(json_data['update_id'])
            return update
        except Exception as e:
            traceback.print_exc()

    def to_json(self) -> Dict[str, any]:
        return {
            'update_id'    : str(self.update_id),
            'update_moment': self.update_moment.strftime(DATE_TIME_FORMAT),
            'update_type'  : self.update_type.name,
            'raw_data'     : self.raw_data
            }

    def __eq__(self, other):
        return self.update_id == other.update_id
