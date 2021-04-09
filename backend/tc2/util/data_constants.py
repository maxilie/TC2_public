from datetime import date

from tc2.util.market_util import OPEN_DURATION

# The number is three candles per minute, which is somewhat arbitrary but nonetheless reasonable to expect.
MIN_CANDLES_PER_MIN = 3
# The minimum number of candles that should be present in a SymbolDay's 'candles' field.
MIN_CANDLES_PER_DAY = (OPEN_DURATION / 60 - 10) * MIN_CANDLES_PER_MIN

# The earliest date to record data for.
START_DATE = date(year=2017, month=1, day=1)

# Enables us to stringify lists and store them inside of other stringified lists.
DATA_SPLITTERS = {'level_1': '$#*a', 'level_2': '$#*b', 'level_3': '$#*c'}


