from enum import Enum


class OrderType(Enum):
    MARKET_BUY = 1
    MARKET_SELL = 2
    LIMIT_BUY = 3
    LIMIT_SELL = 4
    STOP = 5
    UNSUPPORTED = 6
