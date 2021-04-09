import traceback
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict

from tc2.data.data_structs.price_data.Candle import Candle
from tc2.data.data_structs.price_data.DailyCandle import DailyCandle
from tc2.util.TimeInterval import TimeInterval
from tc2.util.data_constants import MIN_CANDLES_PER_MIN
from tc2.util.date_util import DATE_TIME_FORMAT, DATE_FORMAT
from tc2.util.market_util import OPEN_DURATION


class SymbolDay:
    """Contains a day of second-resolution Candle objects."""
    symbol: str
    day_date: date
    candles: List[Candle]

    def __init__(self, symbol: str, day_date: date, candles: List[Candle]) -> None:
        """
        Do NOT instantiate a SymbolDay object directly.
        Instead, MongoManager.load_symbol_day().
        """
        self.symbol = symbol
        self.day_date = day_date
        self.candles = candles
        for candle in self.candles:
            candle.moment = candle.moment.replace(tzinfo=None)

    def get_candle_at_sec(self, moment: datetime) -> Optional[Candle]:
        """Searches for the candle at the given moment."""
        moment = moment
        for candle in self.candles:
            if (candle.moment - moment).total_seconds() < 1:
                return candle
        return None

    def create_daily_candle(self) -> Optional[DailyCandle]:
        """Uses second-resolution candles to aggregate a DailyCandle."""
        if self.candles is None or len(self.candles) == 0:
            return None

        # Search for lowest and highest prices of the day
        day_high = self.candles[0].high
        day_low = self.candles[0].low
        for candle in self.candles:
            if candle.low < day_low:
                day_low = candle.low
            if candle.high > day_high:
                day_high = candle.high

        # Put the stats into a DailyCandle object
        return DailyCandle(day_date=self.day_date,
                           open=self.candles[0].open,
                           high=day_high,
                           low=day_low,
                           close=self.candles[-1].close,
                           volume=sum([candle.volume for candle in self.candles]))

    @classmethod
    def get_ordered_candles(cls, candles: List[Candle], interval: TimeInterval) -> List[Candle]:
        """
        :param candles: a list of candles potentially containing extraneous, unsorted candles
        :return: a list of candles containing only candles contained in this time interval, sorted ascending by date
        """

        # Filter out extraneous candles
        contained_candles = []
        for candle in candles:
            if interval.contains_time(candle.moment.time()):
                contained_candles.append(candle)

        # Sort by date
        contained_candles.sort(key=lambda candle_to_sort: candle_to_sort.moment)
        return contained_candles

    @classmethod
    def validate_candles(cls, candles: List[Candle],
                         min_minutes: int = OPEN_DURATION / 60 - 10,
                         check_secs: bool = True,
                         check_prices: bool = True,
                         max_gap: int = 160,
                         gap_graces: int = 5,
                         debug_output: Optional[List[str]] = None) -> bool:
        """
        :param candles: the data to validate
        :param min_minutes: ensure at least this many minutes have data present during them
        :param check_secs: ensure that each minute has sufficient number of seconds
        :param check_prices: ensure that each candle has positive values
        :param max_gap: the longest duration in seconds to allow for no data to be present more than gap_graces times
        :param gap_graces: the number of gap periods to allow
        :return: True if the list of candles is valid, False otherwise
        """

        if debug_output is not None:
            debug_output.append('validating candles: {}checking seconds in each minute, {}checking prices, '
                                '{} max gap in secs allowed, at least {} minutes needed'
                                .format('' if check_secs else 'not ',
                                        '' if check_prices else 'not ',
                                        max_gap,
                                        min_minutes))

        # Check that minimum number of total seconds are present
        if len(candles) < MIN_CANDLES_PER_MIN * min_minutes:
            if debug_output is not None:
                debug_output.append('needed at least {} * ~{} = {} candles, but only found {}'
                                    .format(MIN_CANDLES_PER_MIN, min_minutes,
                                            MIN_CANDLES_PER_MIN * min_minutes, len(candles)))
            return False

        # Iterate through candle collection to validate it
        secs_in_min_intervals = {}
        longest_gaps = [timedelta(seconds=0) for _ in range(gap_graces + 1)]
        last_t = candles[0].moment
        for candle in candles:
            # Record the second
            # noinspection PyTypeChecker
            sec_moment: datetime = candle.moment.replace(microsecond=0)
            minute_str = sec_moment.replace(second=0).strftime(DATE_TIME_FORMAT)
            if minute_str not in secs_in_min_intervals.keys():
                secs_in_min_intervals[minute_str] = 0
            secs_in_min_intervals[minute_str] += 1

            # Validate price and volume amounts
            if check_prices and \
                    (candle.open < 1 or candle.high < 1 or candle.low < 1 or candle.close < 1 or candle.volume < 1):
                if debug_output is not None:
                    debug_output.append('invalid candle found at {}:{}:{} (OHLCV: {},{},{},{})'
                                        .format(candle.moment.hour, candle.moment.minute, candle.moment.second,
                                                candle.open, candle.high, candle.low, candle.close, candle.volume))
                return False

            # Record time gap between candles
            gap = candle.moment - last_t if last_t.day == candle.moment.day else timedelta(seconds=0)
            for i in range(len(longest_gaps)):
                if longest_gaps[i].total_seconds() > max_gap:
                    continue
                if gap > longest_gaps[i]:
                    longest_gaps[i] = gap
                    break

            # Move on to next candle, mark this one as the "last" one
            last_t = candle.moment

        # Check that minimum number of seconds are present in most every minute
        try:
            if check_secs and \
                    (sorted(list(secs_in_min_intervals.values()))[int(min_minutes / 3.0) + 1] < MIN_CANDLES_PER_MIN):
                if debug_output is not None:
                    debug_output.append(f'too many minutes do not have at least {MIN_CANDLES_PER_MIN} candles; lowest third of minutes:')
                    for num_secs in sorted(list(secs_in_min_intervals.values()))[0:int(min_minutes / 3.0) + 1]:
                        debug_output.append('\t{} candles'.format(num_secs))
                return False
        except Exception as e:
            if debug_output is not None:
                debug_output.append(f'couldn\'t check seconds per minute; most likely this means there are '
                                    f'insufficient minutes or the interval is very small: {traceback.format_exc()}')
            return False

        # Check that the longest gap is not too long
        if longest_gaps[gap_graces].total_seconds() >= max_gap:
            if debug_output is not None:
                debug_output.append(f'unacceptably long gaps found ({longest_gaps[gap_graces].total_seconds()} secs)')
            return False

        if debug_output is not None:
            debug_output.append('candles validated successfully')
        return True

    @classmethod
    def from_json(cls, data: Dict[str, any]) -> Optional['SymbolDay']:
        """Converts the json dictionary into a SymbolDay object."""
        try:
            candles = [Candle.from_json(candle_json) for candle_json in data['candles']]
            return SymbolDay(data['symbol'], data['day_date'], candles)
        except Exception as e:
            traceback.print_exc()
            return None

    def to_json(self) -> Dict[str, any]:
        """Converts the SymbolDay to a json dictionary that can be stored in mongo."""
        return {
            'symbol': self.symbol,
            'day_date': self.day_date.strftime(DATE_FORMAT),
            'candles': [candle.to_json() for candle in self.candles],
        }
