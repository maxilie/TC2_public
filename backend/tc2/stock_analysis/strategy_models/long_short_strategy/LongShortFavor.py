from enum import Enum


class LongShortFavor(Enum):
    """
    A trend strength level of the S&P-500, indicating whether the LongShortStrategy
    should buy more shares of SPXL or SPXS.
    """

    # Split purchase 50/50.
    NO_FAVOR = 0
    # Buy 9% more shares in SPXL.
    SPXL_FAVORED = 1
    # Buy 9% more shares in SPXS.
    SPXS_FAVORED = 2
    # Buy 14% more shares in SPXL.
    SPXL_STRONGLY_FAVORED = 3
    # Buy 14% more shares in SPXS.
    SPXS_STRONGLY_FAVORED = 4
    # Do not evaluate this model for non-S&P symbols.
    NOT_APPLICABLE = 5
