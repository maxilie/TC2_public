import time as pytime
from datetime import datetime, timedelta, time

from tc2.health_checking.HealthCheckResult import HealthCheckResult
from tc2.health_checking.health_check.AbstractHealthCheck import AbstractHealthCheck
from tc2.util.data_constants import START_DATE, MIN_CANDLES_PER_DAY
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.util.rolling_sum_formulas import RollingSumFormulas


class Dip45Check(AbstractHealthCheck):
    """
    Not meant to be accessed except by HealthChecker.
    Checks that the dip_45 produces the expected values and does not fail too many days.

    Conditions for success:
    + At least 1/5th of the days pass the dip45 model_type
    + The rolling sum is in [1, 5]
    """

    # From CycleStrategy.MAX_DIP_45
    MAX_DIP45 = 1.4

    def run(self) -> HealthCheckResult:
        symbol = 'ALXN'
        dates = self.mongo().get_dates_on_file(symbol, START_DATE, self.time().now().date())

        self.debug('max dip45 result for a day to be viable (from CycleStrategy settings): 1.4')
        sample_size = min(120, len(dates) - 1)
        end_index = len(dates) - 1
        start_index = end_index - sample_size
        rolling_sum = 0
        days_passing = 0
        self.debug('analyzing {0} days'.format(sample_size))
        for date_index in range(start_index, end_index):
            # Pause or else gunicorn worker threads will be starved out
            pytime.sleep(0.01)

            # Get data for the day
            day_date = dates[date_index]
            day_data = self.mongo().load_symbol_day(symbol, day_date)

            # Skip if the day has no data
            if len(day_data.candles) < MIN_CANDLES_PER_DAY:
                self.debug('skipping {0}'.format(day_data.day_date))
                continue

            # Find price at minute 60
            start_candle: Candle = day_data.get_candle_at_sec(
                datetime.combine(day_data.day_date, time(hour=10, minute=30)))
            if start_candle is None:
                self.debug("couldn't calculate dip_45 on {0}. Bad data at minute 60".format(day_date))
                continue

            # Find lowest price within 45 minutes after minute 60
            start_time = datetime.combine(day_data.day_date, time(hour=10, minute=30))
            end_time = datetime.combine(day_data.day_date, time(hour=10, minute=30)) + timedelta(
                minutes=45)
            lowest_candle: Candle = Candle(start_candle.moment, start_candle.open, start_candle.high,
                                           start_candle.low,
                                           start_candle.close, start_candle.volume)
            for candle in day_data.candles:
                if candle.low < lowest_candle.low and start_time < candle.moment < end_time:
                    lowest_candle = candle
                    lowest_candle = lowest_candle

            # Calculate the greatest downward price change as a percentage
            strongest_dip = 100.0 * max(0.0, start_candle.low - lowest_candle.low) / start_candle.low
            if strongest_dip > self.MAX_DIP45:
                days_passing += 1

            self.debug('{0} dip on {1}  ({2}viable)'.format("%.2f" % strongest_dip, day_data.day_date,
                                                            'not ' if strongest_dip > self.MAX_DIP45 else ''))

            # Calculate the new rolling sum for the analysis model
            rolling_sum = rolling_sum if strongest_dip == 0 \
                else RollingSumFormulas.combine(rolling_sum, strongest_dip, RollingSumFormulas.get_30_day_weight())

            # Print the new rolling sum
            self.debug('rolling sum is now {0}'.format("%.2f" % rolling_sum))

        # Pass the health check if its conditions are met
        self.set_passing(True)
        if days_passing < (1 / 5) * sample_size:
            self.set_passing(False)
        if not 1 <= rolling_sum <= 5:
            self.set_passing(False)

        return self.make_result()
