import json
import traceback
from datetime import datetime
from typing import Optional, Dict

import pandas as pd

from tc2.data.data_structs.account_data.OrderStatus import OrderStatus
from tc2.data.data_structs.account_data.OrderType import OrderType
from tc2.log.LogFeed import LogFeed, LogLevel
from tc2.util.date_util import DATE_TIME_FORMAT

ORDER_TYPES = {
    'market': {
        'buy': OrderType.MARKET_BUY,
        'sell': OrderType.MARKET_SELL,
    },
    'limit': {
        'buy': OrderType.LIMIT_BUY,
        'sell': OrderType.LIMIT_SELL,
    },
    'stop': {
        'buy': OrderType.STOP,
        'sell': OrderType.STOP
    }
}

ORDER_PRICES = {
    OrderType.MARKET_BUY: 'limit_price',
    OrderType.MARKET_SELL: 'limit_price',
    OrderType.LIMIT_BUY: 'limit_price',
    OrderType.LIMIT_SELL: 'limit_price',
    OrderType.STOP: 'stop_price'
}


class Order:
    """
    An order on the stock market.
    """
    type: OrderType
    status: OrderStatus
    symbol: str
    price: float
    qty: int
    order_id: str
    moment: datetime

    def __init__(self, order_type: OrderType, status: OrderStatus, symbol: str, price: float, qty: int,
                 order_id: str, moment: Optional[datetime] = None) -> None:
        self.type = order_type
        self.status = status
        self.symbol = symbol
        self.price = price
        self.qty = qty
        self.order_id = order_id
        self.moment = datetime.now() if moment is None else moment

    def get_type(self) -> OrderType:
        return self.type

    def get_status(self) -> OrderStatus:
        return self.status

    def get_symbol(self) -> str:
        return self.symbol

    def get_price(self) -> float:
        return self.price

    def get_qty(self) -> int:
        return self.qty

    def get_id(self) -> str:
        return self.order_id

    def get_moment(self) -> datetime:
        return self.moment

    def to_json(self) -> Dict[str, any]:
        return {
            'order_type': self.type.name,
            'status': self.status.name,
            'symbol': self.symbol,
            'price': self.price,
            'qty': self.qty,
            'order_id': self.order_id,
            'moment': self.moment.strftime(DATE_TIME_FORMAT),
        }

    @classmethod
    def from_json(cls, data: Dict[str, any]) -> Optional['Order']:
        try:
            return Order(order_type=OrderType[data['order_type']],
                         status=OrderStatus[data['status']],
                         symbol=data['symbol'],
                         price=float(data['price']),
                         qty=int(data['qty']),
                         order_id=data['order_id'],
                         moment=datetime.strptime(data['moment'], DATE_TIME_FORMAT))
        except Exception as e:
            return None

    @staticmethod
    def from_alpaca_api(data: 'Alpaca Order Entity',
                        logfeed_process: LogFeed) -> Optional['Order']:
        """
        Returns an Order object made from an Alpaca API response.
        See https://docs.alpaca.markets/api-documentation/api-v2/orders/#order-entity.
        """

        # Convert order entity to raw dict, if not already done.
        try:
            data = data._raw
        except Exception as ignored:
            pass

        # Decode order type.
        try:
            order_type = ORDER_TYPES[data['type']][data['side']] \
                if data['type'] in ORDER_TYPES else OrderType.UNSUPPORTED
            if order_type is OrderType.UNSUPPORTED:
                logfeed_process.log(LogLevel.WARNING, f'Couldn\'t decode order: unknown type "{data["type"]}"')
                return None

            # Decode order status.
            st = data['status']
            if st == 'filled' \
                    or st == 'stopped' \
                    or st == 'calculated':
                order_status = OrderStatus.FILLED
            elif st == 'new' \
                    or st == 'partially_filled' \
                    or st == 'done_for_day' \
                    or st == 'accepted' \
                    or st == 'pending_new' \
                    or st == 'accepted_for_bidding':
                order_status = OrderStatus.OPEN
            else:
                order_status = OrderStatus.CANCELED

            # Decode order price.
            try:
                order_price = float(data[ORDER_PRICES[order_type]])
                if data['filled_avg_price'] is not None and data['filled_avg_price'] != '':
                    order_price = float(data['filled_avg_price'])
            except Exception as e:
                order_price = 0.0
                logfeed_process.log(LogLevel.INFO, 'Error decoding order price from {0} \t Error: {1}'
                                    .format(data, traceback.format_exc()))

            return Order(order_type=order_type,
                         status=order_status,
                         symbol=data['symbol'].upper(),
                         price=order_price,
                         qty=int(data['qty']),
                         order_id=data['id'],
                         moment=pd.Timestamp(data['created_at']).to_pydatetime())
        except Exception as e:
            print(f'ERROR DECODING ORDER:')
            print(f'{data}')
            print(f'Raw order:')
            try:
                print(f'{data._raw}')
            except Exception as e:
                print('None')
            traceback.print_exc()
