"""Contains constant variables for CycleStrategy."""

"""
Model constants...
"""

"""
Strategy execution constants...
"""

# Cut losses after losing 0.6%
MAX_STOP_PCT = 0.6

# Place limit-sell orders at least 0.06% above the *latest* price
MIN_SALE_PROFIT = 0.06

# Place limit-sell orders no more than 0.18% above the *latest* price
MAX_SALE_PROFIT = 0.18

# Place a limit-buy order for 0.28% lower than the price at buy time
# TODO Revert this to 0.28 if possible (we're only switching it as a test to increase entry ratio)
LOWER_BUY_PCT = 0.16

# Cancel if price rises 0.35% when we want it to dip
MAX_PCT_INCREASE_BEFORE_BUY = 0.35

# Wait up to 15 minutes before canceling the limit-buy order
MAX_DIP_TIME = 60 * 15

# Leave our most modest order open for only 4 seconds
BASELINE_OPEN_DURATION = 4

# Trade at least $3k at a time
MIN_PURCHASE = 3000
