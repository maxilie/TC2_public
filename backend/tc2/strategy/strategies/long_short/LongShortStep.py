from enum import Enum


class LongShortStep(Enum):
    """
    Defines the order of logical steps to be taken by LongShortStrategy.
    """

    # Wait for price data to come in so we know where to place our buy orders.
    WAIT_FOR_DATA = 1

    # Place slightly low-ball buy orders for both SPXS and SPXL.
    ENTER_SPXS_SPXL = 2

    # Wait for either SPXS or SPXL buy order to go through.
    WAIT_FOR_SINGLE_BUY = 3

    # Sell our position at a tiny profit; hopefully it sells before the other buy order goes through.
    SELL_FIRST_POS_AT_PROFIT = 4

    # Wait for SPXL/SPXS to be bought or SPXS/SPXL to be sold, whichever happens first.
    WAIT_FOR_FIRST_SALE_OR_SECOND_BUY = 5

    # Gradually lower our sell offer(s) until one of them goes through or they are unprofitable.
    LOWER_SALES_TO_BASELINE = 6

    # Sell the remaining position for what we bought it, if possible. Otherwise, sell it at the going rate.
    SELL_AT_MINOR_LOSS = 7
