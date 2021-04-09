import time as pytime
from datetime import timedelta

from tc2.health_checking.HealthCheckResult import HealthCheckResult
from tc2.health_checking.health_check.AbstractHealthCheck import AbstractHealthCheck
from tc2.util.data_constants import START_DATE, MIN_CANDLES_PER_DAY


class DataCheck(AbstractHealthCheck):
    """
    Not meant to be accessed except by HealthChecker.
    Checks that our data is sufficient and that samples of it are valid.

    Conditions for success:
    + 90% of recent days contain the expected number of valid candles
    + 90% of recent days contain no gaps of longer than 45 seconds of data lacking
    """

    DAYS_TO_SAMPLE = 40
    MAX_DISCONTINUITY = 45

    def run(self, symbol: str) -> HealthCheckResult:
        dates = self.mongo().get_dates_on_file(symbol=symbol,
                                               start_date=START_DATE,
                                               end_date=self.time().now().date(),
                                               debug_output=self.debug_messages)

        sample_size = min(self.DAYS_TO_SAMPLE, len(dates) - 1)
        end_index = len(dates) - 1
        start_index = end_index - sample_size
        self.debug('analyzing {0} days for {1}'.format(sample_size, symbol))
        valid_days = 0
        for date_index in range(start_index, end_index):
            # Pause or else gunicorn worker threads will be starved out
            pytime.sleep(0.01)

            # Get data for the day
            day_date = dates[date_index]
            day_data = self.mongo().load_symbol_day(symbol, day_date)

            # Skip if the day has no data
            if len(day_data.candles) < MIN_CANDLES_PER_DAY:
                self.debug('{0} insufficient candles ({1})'.format(day_data.day_date, len(day_data.candles)))
                continue

            # Find the longest gap between updates
            longest_gap = timedelta(seconds=0)
            last_t = day_data.candles[0].moment
            for candle in day_data.candles:
                gap = candle.moment - last_t
                longest_gap = max(gap, longest_gap)
                last_t = candle.moment

            # Check that gap is not too long
            if longest_gap.total_seconds() > self.MAX_DISCONTINUITY:
                continue

            valid_days += 1

            self.debug('{0} longest gap: {1} secs'.format(day_data.day_date, longest_gap.total_seconds()))

        # Pass the health check if its conditions are met
        self.set_passing(True)
        if valid_days < 0.9 * sample_size:
            self.set_passing(False)

        return self.make_result()
