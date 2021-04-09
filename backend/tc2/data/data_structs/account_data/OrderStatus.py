from enum import Enum


class OrderStatus(Enum):
    OPEN = 1
    FILLED = 2
    CANCELED = 3