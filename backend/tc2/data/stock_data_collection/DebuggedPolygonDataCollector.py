from __future__ import annotations

import time as pytime
import traceback
from datetime import datetime, timedelta, date
from statistics import mean
from typing import Optional, List

import alpaca_trade_api as ata
import pandas as pd
from pytz import timezone

from tc2.data.stock_data_collection.AbstractDataCollector import AbstractDataCollector
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.env.TimeEnv import TimeEnv
from tc2.log.LogFeed import LogFeed
from tc2.util.market_util import OPEN_TIME, CLOSE_TIME
from tc2.util.synchronization import synchronized_on_polygon_rest

POLYGON_DATE_FORMAT = '%Y-%m-%d'


class DebuggedPolygonDataCollector(AbstractDataCollector):
    """
    Provides access to stock market data from polygon.io.
    Prints verbose debug messages and timings info.
    """

    # Max number of seconds to wait for polygon rate limit to go away
    MAX_RATE_LIMIT_WAIT = 240

    # Initial number of seconds to wait after encountering API rate limit
    INITIAL_RATE_LIMIT_WAIT = 4

    # Max number of 50k-count batches to fetch before parsing;
    # this number times 50k needs to be higher than the number of trades a stock
    # could have in one second
    MAX_SIMULTANEOUS_BATCHES = 20

    # Instance variables
    next_api_call: datetime
    rate_limit_wait: float

    timings_total: List[float]
    timings_basket: List[float]
    timings_fetch: List[float]
    timings_parse: List[float]
    timings_avg_block1: List[float]
    timings_avg_block2: List[float]
    timings_avg_block3: List[float]
    debug_msgs: List[str]

    def __init__(self, logfeed_program: LogFeed, logfeed_process: LogFeed, time_env: TimeEnv) -> None:
        super().__init__(logfeed_program=logfeed_program,
                         logfeed_process=logfeed_process,
                         time_env=time_env)

        # Private variables
        self.next_api_call = time_env.now()
        self.rate_limit_wait = 0

        # Timings variables
        self.timings_total = []
        self.timings_basket = []
        self.timings_fetch = []
        self.timings_parse = []
        self.timings_avg_block1 = []
        self.timings_avg_block2 = []
        self.timings_avg_block3 = []
        self.debug_msgs = []

    def collect_candles_for_day(self, day: date, symbol: str) -> Optional[SymbolDay]:
        """
        Uses Polygon to collect candles for the given day.
        Does NOT save the newly-collected candles.
        """
        candles = None
        try:
            candles = self._parse_ticks_in_intervals(symbol, [[
                datetime.combine(day, OPEN_TIME),
                datetime.combine(day, CLOSE_TIME)
            ]])
        except Exception as e:
            self.debug_msgs.append(f'Error collecting {symbol} candles from polygon for {day:%m-%d-%Y}:')
            self.debug_msgs.append(traceback.format_exc())

        return SymbolDay(symbol, day, candles)

    @synchronized_on_polygon_rest
    def _parse_ticks_in_intervals(self, symbol: str, intervals: 'list of pairs of ascending dates') -> List[Candle]:
        """
        :param intervals: e.x. [[start_1, end_1], [start_2, end_2]]; lower limits inclusive; upper limits exclusive
        """

        start_total = pytime.monotonic()

        # Set all timezones to EST
        for i in range(len(intervals)):
            intervals[i][0] = timezone('America/New_York').localize(intervals[i][0])
            intervals[i][1] = timezone('America/New_York').localize(intervals[i][1])

        # Parse 50k-count batches of ticks (individual trades) into second-resolution candles
        interval_index = 0
        moment = intervals[interval_index][0].replace(microsecond=0)
        basket_start_moment = moment
        ticks_in_basket = []
        candles = []
        alpaca_client = ata.REST()
        start_basket = pytime.monotonic()
        batches_aggregated = 0
        ns_offset = int(moment.timestamp()) * 1000000000
        while True:

            # Fetch next batch of up to 50k trades, starting at moment
            start_fetch = pytime.monotonic()

            try:

                # Ensure api cooldown is not too long
                if self.next_api_call - self.time_env.now() > timedelta(seconds=self.MAX_RATE_LIMIT_WAIT):
                    self.next_api_call = self.time_env.now() + timedelta(seconds=0.1)
                while self.time_env.now() < self.next_api_call:
                    pytime.sleep(0.5)

                # Request batch of candles from polygon-rest
                self.debug_msgs.append(f'Fetching {symbol} batch starting at {moment:%Y-%m-%d_%H:%M:%S}')
                self.debug_msgs.append(f'\t(ns_offset: {ns_offset}')
                batch_response = alpaca_client.polygon.get(path=f'/ticks/stocks/trades/{symbol}/'
                                                                f'{moment.date().strftime(POLYGON_DATE_FORMAT)}',
                                                           params={'timestamp': ns_offset,
                                                                   'limit': 50000},
                                                           version='v2')
                ticks_in_basket.extend(batch_response['results'])
                batches_aggregated += 1
                ns_offset = ticks_in_basket[-1]['t']
                moment = pd.Timestamp(ns_offset, tz='America/New_York', unit='ns')
                # self.debug_msgs.append(f'Fetched {symbol} batch: it ends at {moment:%H:%M:%S}')

            except Exception as e:

                # On error response, double our wait time before the next query
                self.rate_limit_wait = self.INITIAL_RATE_LIMIT_WAIT if self.rate_limit_wait == 0 \
                    else self.rate_limit_wait * 2

                # Re-attempt to fetch after applying the wait time
                if self.rate_limit_wait <= self.MAX_RATE_LIMIT_WAIT:
                    self.next_api_call = self.time_env.now() + timedelta(seconds=self.rate_limit_wait)
                    self.timings_fetch.append(pytime.monotonic() - start_fetch)
                    self.timings_basket.append(pytime.monotonic() - start_basket)
                    self.debug_msgs.append(
                        f'Error collecting a batch of data from polygon-rest: {traceback.format_exc()}')
                    # Re-attempt to collect this data
                    continue

            # On too many error responses and empty basket, end task
            if self.rate_limit_wait > self.MAX_RATE_LIMIT_WAIT and len(ticks_in_basket) == 0:
                self.debug_msgs.append(
                    f'WARNING: Couldn\'t collect {symbol} candles from polygon starting on {moment:%d-%m-%Y} '
                    f'at {moment:%H:%M:%S}! Stopping collection early')
                return candles
            # On too many error responses and nonempty basket, finish parsing basket and then end task
            elif self.rate_limit_wait > self.MAX_RATE_LIMIT_WAIT:
                pass
            # On out of market-hours batch, finish parsing basket and then end task
            elif moment > timezone('America/New_York').localize(datetime.combine(moment.date(), CLOSE_TIME)):
                self.rate_limit_wait = self.MAX_RATE_LIMIT_WAIT
            # On few or no error responses, keep fetching until basket fills up
            elif batches_aggregated <= self.MAX_SIMULTANEOUS_BATCHES \
                    and self.rate_limit_wait <= self.MAX_RATE_LIMIT_WAIT \
                    and moment <= timezone('America/New_York').localize(
                datetime.combine(moment.date(), CLOSE_TIME) + timedelta(minutes=45)):
                continue
            # On empty basket and termination condition, return what we have
            elif len(ticks_in_basket) == 0:
                break

            # Aggregate ticks from the API response into second-resolution Candle objects
            start_parse = pytime.monotonic()
            prices_in_moment = []
            volume_in_moment = 0
            timings_block1 = []
            timings_block2 = []
            timings_block3 = []
            candles_before_basket = len(candles)
            moment = basket_start_moment
            for tick_data in ticks_in_basket:
                start_block1 = pytime.monotonic()
                tick_moment = pd.Timestamp(tick_data['t'], tz='America/New_York', unit='ns').to_pydatetime()
                if tick_moment < moment:
                    # Skip over trades made before the truncated second
                    timings_block1.append(pytime.monotonic() - start_block1)
                    continue
                timings_block1.append(pytime.monotonic() - start_block1)
                start_block2 = pytime.monotonic()
                timings_block2.append(pytime.monotonic() - start_block2)
                start_block3 = pytime.monotonic()
                if tick_moment < moment + timedelta(seconds=1):
                    # Count this trade toward the candle during which it was made
                    prices_in_moment.append(tick_data['p'])
                    volume_in_moment += tick_data['s']
                else:
                    # At the end of the second (i.e. x.999),
                    # use the accumulated trades to create a Candle object
                    if len(prices_in_moment) > 0 and volume_in_moment > 0:
                        candle = Candle(moment=moment.replace(tzinfo=None),
                                        open=prices_in_moment[0],
                                        high=max(prices_in_moment),
                                        low=min(prices_in_moment),
                                        close=prices_in_moment[-1],
                                        volume=volume_in_moment)
                        # Store the candle
                        if OPEN_TIME <= candle.moment.time() < CLOSE_TIME:
                            candles.append(candle)
                    # Move on to the next truncated second, starting with this trade
                    prices_in_moment = [tick_data['p']]
                    volume_in_moment = tick_data['s']
                    moment = tick_moment.replace(microsecond=0)
                timings_block3.append(pytime.monotonic() - start_block3)

            # Print timings and debug info on this basket
            self.timings_parse.append(pytime.monotonic() - start_parse)
            self.timings_basket.append(pytime.monotonic() - start_basket)
            if len(timings_block1) > 5:
                self.timings_avg_block1.append(mean(timings_block1))
            if len(timings_block2) > 5:
                self.timings_avg_block2.append(mean(timings_block2))
            if len(timings_block3) > 5:
                self.timings_avg_block3.append(mean(timings_block3))
            if len(candles) == candles_before_basket:
                self.debug_msgs.append('WARNING: NO CANDLES PARSED FOR THIS BASKET')
            else:
                self.debug_msgs.append(f'Total candles parsed this basket: {len(candles) - candles_before_basket}')
                self.debug_msgs.append(
                    f'First candle parsed: {candles[candles_before_basket].moment:%Y-%m-%d_%H:%M:%S}')
                self.debug_msgs.append(f'Last candle parsed: {candles[-1].moment:%Y-%m-%d_%H:%M:%S}')

            # Move to the next second if fetching this basket ended in errors or an empty basket
            if self.rate_limit_wait > self.MAX_RATE_LIMIT_WAIT or len(candles) == candles_before_basket:
                basket_start_plus_1 = basket_start_moment + timedelta(seconds=1)
                last_parsed_plus_1 = moment + timedelta(seconds=1)
                moment = basket_start_plus_1 if basket_start_plus_1 > last_parsed_plus_1 else last_parsed_plus_1

            # When moment advances beyond current interval, jump to next interval or end task
            if ns_offset >= intervals[interval_index][1].timestamp() * 1000000000:

                # Return after collecting candles for the final time interval
                if interval_index == len(intervals) - 1:
                    self.debug_msgs.append('Ending polygon task after exceeding the final time interval')
                    break

                # Move on to the next time interval
                else:
                    self.debug_msgs.append(
                        f'Polygon task advancing to next time interval, moment = {moment:%m-%d-%Y_%H:%M:%S}')
                    interval_index += 1
                    moment = intervals[interval_index][0]

            # Reset basket data so the next batches can be fetched
            batches_aggregated = 0
            self.rate_limit_wait = 0
            basket_start_moment = moment
            ns_offset = int(moment.timestamp()) * 1000000000
            ticks_in_basket = []

        self.timings_total.append(pytime.monotonic() - start_total)
        return candles
