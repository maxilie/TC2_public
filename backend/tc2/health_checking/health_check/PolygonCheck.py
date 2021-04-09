from statistics import mean

from tc2.data.stock_data_collection.DebuggedPolygonDataCollector import DebuggedPolygonDataCollector
from tc2.data.stock_data_collection.PolygonDataCollector import PolygonDataCollector
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.health_checking.HealthCheckResult import HealthCheckResult
from tc2.health_checking.health_check.AbstractHealthCheck import AbstractHealthCheck


class PolygonCheck(AbstractHealthCheck):
    """
    Not meant to be accessed except by HealthChecker.
    Checks that the program can successfully fetch stock market data from polygon.io.

    Conditions for success:
    + Data query returns a full, valid day's worth of price data.
    """

    def run(self) -> HealthCheckResult:
        try:
            # Fetch candles from the previous market day
            symbol = 'SPY'
            day_date = self.time().get_prev_mkt_day()
            # noinspection PyTypeChecker
            polygon_collector = DebuggedPolygonDataCollector(None, None, self.time())
            self.debug(f'Collecting {symbol} data from polygon for {day_date:%m-%d-%Y}')
            day_data = polygon_collector.collect_candles_for_day(day=day_date, symbol=symbol)
            self.debug_messages.extend(polygon_collector.debug_msgs)

            # Print timings
            self.set_passing(True)
            time_length = '--' if len(polygon_collector.timings_total) == 0 \
                else f'{mean(polygon_collector.timings_total) / 60.0:.2}m'
            if mean(polygon_collector.timings_total) > 60 * 7:
                self.debug('POLYGON CHECK FAILED: It takes more than 7 minutes to fetch a day of data')
            self.debug(f'Avg total task time: {time_length}')
            time_length = '--' if len(polygon_collector.timings_basket) == 0 \
                else f'{mean(polygon_collector.timings_basket):.2f}s'
            self.debug(f'Avg total basket handling time: {time_length}')
            time_length = '--' if len(polygon_collector.timings_fetch) == 0 \
                else f'{mean(polygon_collector.timings_fetch):.2f}s'
            self.debug(f'Avg batch fetch time: {time_length}')
            time_length = '--' if len(polygon_collector.timings_parse) == 0 \
                else f'{mean(polygon_collector.timings_parse):.2f}s'
            self.debug(f'Avg basket parse time: {time_length}')
            time_length = '--' if len(polygon_collector.timings_avg_block1) == 0 \
                else f'{mean(polygon_collector.timings_avg_block1) * 1000:.2}ms'
            self.debug(f'Avg block1 logic time: {time_length}')
            time_length = '--' if len(polygon_collector.timings_avg_block2) == 0 \
                else f'{mean(polygon_collector.timings_avg_block2) * 1000:.2}ms'
            self.debug(f'Avg block2 logic time: {time_length}')
            time_length = '--' if len(polygon_collector.timings_avg_block3) == 0 \
                else f'{mean(polygon_collector.timings_avg_block3) * 1000:.2}ms'
            self.debug(f'Avg block3 logic time: {time_length}')

            # Check with production version of PolygonDataCollector
            self.debug(f'Now collecting the same data using the production data collector...')
            polygon_collector = PolygonDataCollector(logfeed_program=self.logfeed_process,
                                                     logfeed_process=self.logfeed_process,
                                                     time_env=self.time())
            day_data = polygon_collector.collect_candles_for_day(day=day_date, symbol=symbol)


            # Pass the model_type if collected data is valid
            if day_data is None or not SymbolDay.validate_candles(day_data.candles, debug_output=self.debug_messages):
                self.debug('Polygon query returned invalid candles')
                self.set_passing(False)
            else:
                self.debug('Production data collector returned valid data')
        except Exception as e:
            self.debug('Error fetching polygon data: {}'.format(e.args))
            self.set_passing(False)

        return self.make_result()
