"""Contains constant variables for LongShortStrategy."""

# The amount of time during which oscillatory behavior must be seen before buying.
OSCILLATION_PERIOD_LENGTH = 6 * 60

# The dollar amount of each SPXL, SPXS to trade.
SPXL_SPXS_SIZE = 10000

# The pct below current value to place our initial buy order for SPXL.
SPXL_BUY_DIP_PCT = 0.08

# The tiny pct profit to quickly target for SPXL if it gets bought before SPXS.
SPXL_INITIAL_PROFIT_TARGET_PCT = 0.06

# The greedy pct profit to target for SPXL once both SPXL and SPXS have been bought.
# TODO Make this value 80% of the oscillation period
SPXL_MAX_PROFIT_TARGET_PCT = 0.13

# The percent loss to tolerate before immediately selling a symbol.
KILLSWITCH_ACTIVATION_PCT = 1.85

# The time to wait for the first buy order to get filled.
INITIAL_BUY_WAIT_TIME = 120

# The time to wait for SPXL to get bought.
FIRST_BUY_OR_SECOND_SALE_WAIT_TIME = 180

# The time to wait for one of SPXL or SPXS to sell before lowering our sell orders.
INITIAL_SELL_WAIT_TIME = 30

# The time to spend incrementally lowering sell offers until one goes through.
NEGOTIATION_TIME = 140

# The amount of time to hold a baseline sell order on the second position before letting it go at a loss.
FINAL_OPTIMISM_TIME = 180

# The number of seconds before markets close to dump shares.
DUMP_WINDOW_SECS = 30 * 60
