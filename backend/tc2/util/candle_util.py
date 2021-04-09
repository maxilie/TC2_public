from datetime import date, datetime, timedelta
from statistics import mean, stdev
from typing import List, Optional, Tuple

from tc2.data.data_structs.price_data.Candle import Candle
from tc2.data.data_structs.price_data.MinuteCandle import MinuteCandle
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.util.TimeInterval import ContinuousTimeInterval, TimeInterval


def candles_in_period(period: ContinuousTimeInterval,
                      all_candles: List[Candle],
                      day_date: date) -> List[Candle]:
    """
    Returns the subset of all_candles contained in the given time interval.
    """
    start_moment = datetime.combine(day_date, period.start_time)
    end_moment = datetime.combine(day_date, period.end_time)
    return [candle for candle in all_candles if start_moment <= candle.moment <= end_moment]


def min_candle_in_period(period: ContinuousTimeInterval,
                         candles: List[Candle],
                         day_date: date) -> Optional[Candle]:
    """
    Returns the candle on day_date with the lowest price during the time period.
    """
    lowest_candle: Optional[Candle] = None

    # Define the range in terms of datetimes.
    start_moment = datetime.combine(day_date, period.start_time)
    end_moment = datetime.combine(day_date, period.end_time)

    # Search through each candle for the lowest one.
    for candle in candles:
        if start_moment <= candle.moment <= end_moment and \
                (lowest_candle is None or candle.low < lowest_candle.low):
            lowest_candle = candle

    # Return the candle with the lowest price.
    return lowest_candle


def max_candle_in_period(period: ContinuousTimeInterval,
                         candles: List[Candle],
                         day_date: date) -> Optional[Candle]:
    """
    Returns the candle on day_date with the highest price during the time period.
    """
    highest_candle: Optional[Candle] = None

    # Define the range in terms of datetimes.
    start_moment = datetime.combine(day_date, period.start_time)
    end_moment = datetime.combine(day_date, period.end_time)

    # Search through each candle for the highest one.
    for candle in candles:
        if start_moment <= candle.moment <= end_moment and \
                (highest_candle is None or candle.high > highest_candle.high):
            highest_candle = candle

    # Return the candle with the highest price.
    return highest_candle


def midpoint_candle_in_period(period: ContinuousTimeInterval,
                              candles: List[Candle],
                              day_date: date) -> Optional[Candle]:
    """
    Returns the candle on day_date at the time that is nearest to the period's midpoint.
    """
    midpoint_moment = (datetime.combine(day_date, period.start_time) + timedelta(seconds=period.length() / 2))
    med_candle: Optional[Candle] = None

    # Define the range in terms of datetimes.
    start_moment = datetime.combine(day_date, period.start_time)
    end_moment = datetime.combine(day_date, period.end_time)

    # Search through each candle for the one that is nearest to the midpoint moment.
    for candle in candles:
        if start_moment <= candle.moment <= end_moment and \
                (med_candle is None or candle.moment - midpoint_moment < med_candle.moment - midpoint_moment):
            med_candle = candle

    # Return the midpoint candle.
    return med_candle


def aggregate_minute_candles(candles: List[Candle]) -> List[MinuteCandle]:
    """
    Aggregates the list of second-resolution Candles into a list of minute-resolution MinuteCandles.
    """
    if len(candles) == 0:
        return []

    minute_candles = []
    last_min = candles[0].moment.replace(second=0)
    last_open = candles[0].open
    last_high = candles[0].high
    last_low = candles[0].low
    last_close = candles[0].close
    last_vol = 0
    for candle in candles:
        # Store the aggregated candle and move to the next minute.
        if candle.moment > last_min + timedelta(seconds=60):
            if last_open != 0:
                minute_candles.append(MinuteCandle(minute=last_min,
                                                   open=last_open,
                                                   high=last_high,
                                                   low=last_low,
                                                   close=last_close,
                                                   volume=last_vol))
            last_min = (last_min + timedelta(seconds=61)).replace(second=0)
            last_open = 0
            last_high = 0
            last_low = 0
            last_close = 0
            last_vol = 0
            continue

        # Set the minute's close to the most recent second's close.
        last_close = candle.close

        # Start a new aggregated minute candle.
        if last_open == 0:
            last_open = candle.open
            last_high = candle.high
            last_low = candle.low

        # Accumulate volume and check if this second reached a new high or low.
        last_vol += candle.volume
        if candle.high > last_high:
            last_high = candle.high
        if candle.low < last_low:
            last_low = candle.low

    # Save the last candle after looping completes.
    if last_open != 0:
        minute_candles.append(MinuteCandle(minute=last_min,
                                           open=last_open,
                                           high=last_high,
                                           low=last_low,
                                           close=last_close,
                                           volume=last_vol))

    # Return the minute candles.
    return minute_candles


def init_simulation_data(live_env: 'ExecEnv',
                         sim_env: 'ExecEnv',
                         symbols: List[str],
                         days: int,
                         end_date: date,
                         model_feeder: 'ModelFeeder',
                         skip_last_day_training: bool = False) -> Optional[str]:
    """
    WARNING: this will change the time of the simulated environment, sim_env.

    :param days: the number of market days to fill with data before (including) end_date
    :param skip_last_day_training: whether or not to skip training analysis models on end_date
    Copies live data into the simulation environment and trains analysis models.
    Returns None if successful. Otherwise the error message is returned.
    """

    # Go back n days from end_date.
    day_date = end_date
    for i in range(days):
        day_date = live_env.time().get_prev_mkt_day(day_date)

    # Copy data for each day into simulation environment and train models.
    for i in range(days + 1):
        for symbol in symbols:
            # Load data from live environment.
            day_data = live_env.mongo().load_symbol_day(symbol=symbol, day=day_date)

            # Validate data.
            if not SymbolDay.validate_candles(day_data.candles):
                return f'Couldn\'t set up {days}-day simulation environment for {symbol} ending at ' \
                       f'{end_date:%Y-%m-%d}. Data missing on {day_date:%Y-%m-%d}'

            # Copy data into the simulated environment.
            sim_env.mongo().save_symbol_day(day_data)

            # Train models.
            if day_date != end_date or not skip_last_day_training:
                model_feeder.train_models(symbol=symbol,
                                          day_date=day_date,
                                          day_data=day_data,
                                          stable=True)

        # Move to the next day.
        day_date = live_env.time().get_next_mkt_day(day_date)


def get_steady_range(candles: List[Candle],
                     percentile: float = 0.95) -> Tuple[float, float]:
    """
    Returns the bottom nth percentile price and the top nth percentile price of a range.
    """

    assert 0.5 < percentile < 1
    assert len(candles) > 5, 'Steady range calculation requires at least 5 candles'

    # Order lows descending and highs ascending
    lows = sorted([0.3 * candle.open + 0.7 * candle.low for candle in candles], reverse=True)
    highs = sorted([0.3 * candle.open + 0.7 * candle.high for candle in candles])

    # Get nth percentile of low and high prices
    low_steady = lows[int(len(lows) * percentile)]
    high_steady = highs[int(len(highs) * percentile)]

    return low_steady, high_steady


def find_mins_maxs(trendline_candles: List[Candle]) -> Tuple[List[Candle], List[Candle]]:
    """
    Returns two lists: the first containing local minima, and the second local maxima.
    """
    # Sanitize input.
    assert len(trendline_candles) > 9, 'Cannot find mins/maxs without at least 10 candles'
    # Get sliding window length.
    trend_length = ContinuousTimeInterval(start_time=trendline_candles[0].moment.time(),
                                          end_time=trendline_candles[-1].moment.time()).length()
    window_length = max(5, int(trend_length * 0.12))
    # Ensure sliding window length is an odd number of seconds.
    window_length = window_length if window_length % 2 == 0 else window_length + 1

    # Get slide interval.
    slide_interval = max(1, window_length * 0.02)

    # Slide the window along the trendline period.
    mins, maxs = [], []
    window = ContinuousTimeInterval(trendline_candles[0].moment.time(),
                                    (trendline_candles[0].moment + timedelta(seconds=window_length)).time())
    while datetime.combine(trendline_candles[0].moment.date(), window.end_time) <= trendline_candles[-1].moment:
        # Get candles in the window.
        window_candles = SymbolDay.get_ordered_candles(candles=trendline_candles,
                                                       interval=TimeInterval(None, window.start_time, window.end_time))
        # Get midpoint candle.
        midpoint_candle = midpoint_candle_in_period(period=window,
                                                    candles=trendline_candles,
                                                    day_date=trendline_candles[0].moment.date())
        # Get candles before and after the midpoint.
        first_half_candles = [candle for candle in window_candles if candle.moment < midpoint_candle.moment]
        second_half_candles = [candle for candle in window_candles if candle.moment > midpoint_candle.moment]

        # Ensure there are candles before/after the midpoint.
        if midpoint_candle is None or len(window_candles) == 0 or len(first_half_candles) == 0 \
                or len(second_half_candles) == 0:
            # Slide the window forward if not enough candles.
            window_start = datetime.combine(datetime.today(), window.start_time) + timedelta(seconds=slide_interval)
            window_end = datetime.combine(datetime.today(), window.end_time) + timedelta(seconds=slide_interval)
            window = ContinuousTimeInterval(window_start.time(), window_end.time())
            continue

        # Find out what percentage of prices before/after midpoint are less than the midpoint price.
        pct_prices_below = (len([candle for candle in first_half_candles if candle.low < midpoint_candle.low])
                            + len([candle for candle in second_half_candles if candle.low < midpoint_candle.low])) \
                           / len(window_candles)
        # Find out what percentage of prices before/after midpoint are greater than the midpoint price.
        pct_prices_above = (len([candle for candle in first_half_candles if candle.high > midpoint_candle.high])
                            + len([candle for candle in second_half_candles if candle.high > midpoint_candle.high])) \
                           / len(window_candles)

        # Record a local minimum if 97% of the window's prices are higher than the midpoint price.
        if pct_prices_above >= 0.97:
            mins.append(midpoint_candle)

        # Record a local maximum if 97% of the window's prices are lower than the midpoint price.
        if pct_prices_below >= 0.97:
            maxs.append(midpoint_candle)

        # Slide the window forward.
        window_start = datetime.combine(datetime.today(), window.start_time) + timedelta(seconds=slide_interval)
        window_end = datetime.combine(datetime.today(), window.end_time) + timedelta(seconds=slide_interval)
        window = ContinuousTimeInterval(window_start.time(), window_end.time())

    # Get candles at the beginning and end of the trendline period.
    start_candles = SymbolDay.get_ordered_candles(
        candles=trendline_candles,
        interval=TimeInterval(None, trendline_candles[0].moment.time(),
                              (trendline_candles[0].moment + timedelta(seconds=window_length)).time()))
    end_candles = SymbolDay.get_ordered_candles(
        candles=trendline_candles,
        interval=TimeInterval(None, (trendline_candles[-1].moment - timedelta(seconds=window_length)).time(),
                              trendline_candles[-1].moment.time()))

    # Check for a global minimum in prices at the start and end of the trendline period.
    start_min = sorted(start_candles, key=lambda candle: candle.low)[0]
    end_min = sorted(end_candles, key=lambda candle: candle.low)[0]
    if len(mins) < 2 or start_min.low < min([local_min_candle.low for local_min_candle in mins]):
        mins.insert(0, start_min)
    if len(mins) < 2 or end_min.low < min([local_min_candle.low for local_min_candle in mins]):
        mins.append(end_min)

    # Check for a global maximum in prices at the start and end of the trendline period.
    start_max = sorted(start_candles, key=lambda candle: candle.high)[-1]
    end_max = sorted(end_candles, key=lambda candle: candle.high)[-1]
    if len(maxs) < 2 or start_max.high > max([local_max_candle.high for local_max_candle in maxs]):
        maxs.insert(0, start_max)
    if len(maxs) < 2 or end_max.high > max([local_max_candle.high for local_max_candle in maxs]):
        maxs.append(end_max)

    # Ensure minima are spread apart by at least 3% of the trendline's period.
    reqd_dist = max(3, trend_length * 0.03)
    i = 0
    while i < len(mins) - 1 and len(mins) >= 3:
        if (mins[i + 1].moment - mins[i].moment).total_seconds() < reqd_dist:
            # Remove the higher of the two local minima
            mins.pop(i if mins[i].low > mins[i + 1].low else i + 1)
        else:
            i += 1

    # Ensure maxima are spread apart by at least 3% of the trendline's period.
    i = 0
    while i < len(maxs) - 1 and len(maxs) >= 3:
        if (maxs[i + 1].moment - maxs[i].moment).total_seconds() < reqd_dist:
            # Remove the lower of the two local maxima.
            maxs.pop(i if maxs[i].high < maxs[i + 1].high else i + 1)
        else:
            i += 1

    return mins, maxs

def candles_to_sents(candles: List[Candle],
                     min_sent_length_secs: int = 30,
                     max_sent_length_secs: int = 60 * 5) -> List[List[float]]:
    """
    Returns a list containing lists of percent changes in price over consecutive moments.
    """

    # Drop low-volume data.
    vol_mean = mean([candle.volume for candle in candles])
    vol_stdev = stdev([candle.volume for candle in candles])
    candles = [candle for candle in candles if abs(candle.volume - vol_mean) < vol_stdev * 1.7]

    # Break up non-consecutive candles.
    price_sents = []
    sent_start_idx = 0
    for i in range(1, len(candles)):
        if candles[i].moment - candles[i - 1].moment > timedelta(seconds=2):
            price_sents.append([candle.open for candle in candles[sent_start_idx:i]])
            sent_start_idx = i + 1

    # Ensure each sentence covers at least two periods.
    SECS_IN_PERIOD = 2
    price_sents = [sent for sent in price_sents if len(sent) >= 2 * SECS_IN_PERIOD]

    # Drop short sentences.
    price_sents = [sent for sent in price_sents if len(sent) >= min_sent_length_secs]

    # Enforce min/max sentence length.
    adj_price_sents = []
    for sent in price_sents:
        if len(sent) < min_sent_length_secs:
            continue
        elif len(sent) < max_sent_length_secs:
            adj_price_sents.append(sent)
        while len(sent) > max_sent_length_secs:
            adj_price_sents.append(sent[:max_sent_length_secs])
            if len(sent[max_sent_length_secs:]) > min_sent_length_secs:
                adj_price_sents.append(sent[max_sent_length_secs:])

    # TODO Average prices over each 2-second period.

    # TODO Calculate pct change between each period.
    sentences = []
    return sentences
