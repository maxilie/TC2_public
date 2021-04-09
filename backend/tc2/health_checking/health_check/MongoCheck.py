import time as pytime
from datetime import date, datetime, timedelta
from statistics import mean

from tc2.health_checking.HealthCheckResult import HealthCheckResult
from tc2.health_checking.health_check.AbstractHealthCheck import AbstractHealthCheck
from tc2.util.data_constants import MIN_CANDLES_PER_DAY, START_DATE
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.util.date_util import DATE_FORMAT
from tc2.util.market_util import OPEN_TIME


class MongoCheck(AbstractHealthCheck):
    """
    Not meant to be accessed except by HealthChecker.
    Checks that mongo lookup speed is fast enough.

    Conditions for success:
    + Mongo data is present after saving it
    + Later data is present after call to remove_days_before()
    + Earlier data is present after call to remove_days_after()
    + Mongo load time for a day of data is less than 150ms
    TODO Mongo saving passes a concurrency test (saving multiple days at the same time from separate threads)
    """

    MAX_LOAD_TIME = 250

    def run(self) -> HealthCheckResult:
        # Settings
        dummy_symbl = 'DUMMY'
        dummy_2_symbl = 'DUMMY2'
        num_candles = int(MIN_CANDLES_PER_DAY)

        # Get 5 market dates to populate with dummy data in the test database
        market_dates = []
        market_date = date(year=2019, month=1, day=1)
        while len(market_dates) != 5:
            market_date = self.time().get_next_mkt_day(market_date)
            market_dates.append(market_date)

        mongo = self.sim_env.mongo()

        # Save data on DUMMY2 to test whether operations on DUMMY affect it
        dummy_2_data = self.create_dummy_day(dummy_2_symbl, market_dates[0], num_candles)
        mongo.save_symbol_day(dummy_2_data,
                              debug_output=self.debug_messages)

        # Create SymbolDay's
        dummy_day_datas = [self.create_dummy_day(dummy_symbl, dummy_date, num_candles) for dummy_date in market_dates]

        # Save SymbolDay's
        for day_data in dummy_day_datas:
            mongo.save_symbol_day(day_data,
                                  debug_output=self.debug_messages)

        # Record time it takes to load each day of dummy data
        load_times = []
        candles_loaded = []
        for i in range(5):
            self.debug('loading data for saved day #{}/{}: {}'.format(i + 1, 5, market_dates[i].strftime(DATE_FORMAT)))
            start_instant = pytime.monotonic()
            loaded_day_data = mongo.load_symbol_day(dummy_symbl, market_dates[i],
                                                    debug_output=self.debug_messages)
            load_times.append((pytime.monotonic() - start_instant) * 1000.0)
            candles_loaded.append(0 if loaded_day_data is None else len(loaded_day_data.candles))

        # Calculate stats on data loading
        min_candles = min(candles_loaded)
        max_candles = max(candles_loaded)
        avg_load_time = mean(load_times)

        # Test functionality of mongo.delete_days_before()
        self.debug('deleting days before {}'.format(market_dates[1].strftime(DATE_FORMAT)))
        mongo.remove_price_data_before(dummy_symbl, market_dates[1],
                                       debug_output=self.debug_messages)
        self.debug('checking that the day before {} was removed'.format(market_dates[1].strftime(DATE_FORMAT)))
        dates_on_file = mongo.get_dates_on_file(dummy_symbl,
                                                start_date=START_DATE,
                                                end_date=self.time().now().date(),
                                                debug_output=self.debug_messages)
        delete_before_effective = market_dates[0] not in dates_on_file
        delete_before_discriminate = True
        for day_date in market_dates[1:]:
            if day_date not in dates_on_file:
                self.debug('call to mongo.remove_days_before() deleted too many dates_on_file')
                delete_before_discriminate = False
                break
            day_data = mongo.load_symbol_day(dummy_symbl, day_date,
                                             debug_output=self.debug_messages)
            if day_data is None or len(day_data.candles) == 0:
                self.debug('call to mongo.remove_days_before() deleted too many days from the candle collection')
                delete_before_discriminate = False
                break

        # Test functionality of mongo.delete_days_after()
        self.debug('deleting days after {}'.format(market_dates[-2].strftime(DATE_FORMAT)))
        mongo.remove_price_data_after(dummy_symbl, market_dates[-2], self.time().now().today(),
                                      debug_output=self.debug_messages)
        self.debug('checking that the day after {} was removed'.format(market_dates[-2].strftime(DATE_FORMAT)))
        dates_on_file = mongo.get_dates_on_file(dummy_symbl,
                                                start_date=START_DATE,
                                                end_date=self.time().now().date(),
                                                debug_output=self.debug_messages)
        delete_after_effective = market_dates[-1] not in dates_on_file
        delete_after_discriminate = True
        for day_date in market_dates[-2:-4:-1]:
            if day_date not in dates_on_file:
                self.debug('call to mongo.remove_days_after() deleted too many dates_on_file')
                delete_after_discriminate = False
                break
            day_data = mongo.load_symbol_day(dummy_symbl, day_date,
                                             debug_output=self.debug_messages)
            if day_data is None or len(day_data.candles) == 0:
                self.debug('call to mongo.remove_days_after() deleted too many days from the candle collection')
                delete_after_discriminate = False
                break

        # Test functionality of mongo.drop_symbol_day()
        self.debug('deleting single day: {}'.format(market_dates[2].strftime(DATE_FORMAT)))
        mongo.price_worker._drop_day_data(dummy_symbl, market_dates[2],
                             debug_output=self.debug_messages)
        dates_on_file = mongo.get_dates_on_file(dummy_symbl,
                                                start_date=START_DATE,
                                                end_date=self.time().now().date(),
                                                debug_output=self.debug_messages)
        delete_single_effective = market_dates[2] not in dates_on_file \
                                  and len(mongo.load_symbol_day(dummy_symbl, market_dates[2],
                                                                debug_output=self.debug_messages).candles) == 0

        # Test functionality of mongo.drop_symbol
        self.debug('dropping entire symbol')
        mongo.drop_symbol(dummy_symbl)
        dates_on_file = mongo.get_dates_on_file(dummy_symbl,
                                                start_date=START_DATE,
                                                end_date=self.time().now().date(),
                                                debug_output=self.debug_messages)
        drop_effective = len(dates_on_file) == 0
        for day_date in market_dates:
            if len(mongo.load_symbol_day(dummy_symbl, day_date,
                                         debug_output=self.debug_messages).candles) != 0:
                drop_effective = False
                break

        # Test whether operations on DUMMY affected data for DUMMY2
        operations_independent = True
        dates_on_file = mongo.get_dates_on_file(dummy_2_symbl,
                                                start_date=START_DATE,
                                                end_date=self.time().now().date(),
                                                debug_output=self.debug_messages)
        if market_dates[0] not in dates_on_file:
            self.debug('operations on {} removed dates_on_file for {}'.format(dummy_symbl, dummy_2_symbl))
            operations_independent = False
        dummy_2_data = mongo.load_symbol_day(dummy_2_symbl, market_dates[0],
                                             debug_output=self.debug_messages)
        if dummy_2_data is None or len(dummy_2_data.candles) != num_candles:
            self.debug('operations on {} removed candle data for {}'.format(dummy_symbl, dummy_2_symbl))
            operations_independent = False

        # Display that results
        self.debug('Candles loaded: expected / actual min / actual max: {} / {} / {}'.format(num_candles, min_candles,
                                                                                             max_candles))
        self.debug('Average load time: {0}ms'.format('%.0f' % avg_load_time))

        # Pass the health check if its conditions are met
        self.set_passing(True)
        if min_candles != max_candles:
            self.debug('FAILURE: saving is unreliable (different numbers of candles '
                       'were loaded on different dates even though the same number was saved each day')
            self.set_passing(False)
        if min_candles != num_candles:
            self.debug('FAILURE: saved {} candles but only loaded back {} of them'.format(num_candles, min_candles))
            self.set_passing(False)
        if avg_load_time > self.MAX_LOAD_TIME:
            self.debug('FAILURE: average load time too high')
            self.set_passing(False)
        if not delete_before_effective:
            self.debug('FAILURE: mongo.delete_days_before() is ineffective (does not actually delete days before)')
            self.set_passing(False)
        if not delete_before_discriminate:
            self.debug('FAILURE: mongo.delete_days_before() is indiscriminate (deletes more than it should)')
            self.set_passing(False)
        if not delete_after_effective:
            self.debug('FAILURE: mongo.delete_days_after() is ineffective (does not actually delete days before)')
            self.set_passing(False)
        if not delete_after_discriminate:
            self.debug('FAILURE: mongo.delete_days_after() is indiscriminate (deletes more than it should)')
            self.set_passing(False)
        if not delete_single_effective:
            self.debug('FAILURE: mongo._drop_symbol_day() did not remove the day\'s data')
            self.set_passing(False)
        if not drop_effective:
            self.debug('FAILURE: mongo.drop_symbol() did not remove all the symbol\'s data')
            self.set_passing(False)
        if not operations_independent:
            self.debug('FAILURE: saving/deleting operations for one symbol somehow affected the data of another')
            self.set_passing(False)

        return self.make_result()

    def create_dummy_day(self, symbol: str, day_date: date, num_candles: int) -> SymbolDay:
        """Creates a SymbolDay with mock price data."""
        dummy_candles = []
        dummy_moment = datetime.combine(day_date, OPEN_TIME)
        for i in range(num_candles):
            dummy_candles.append(Candle(moment=dummy_moment,
                                        open=0.001,
                                        high=0.001,
                                        low=0.001,
                                        close=0.001,
                                        volume=999,
                                        ))
            dummy_moment += timedelta(seconds=1)
        return SymbolDay(symbol, day_date, dummy_candles)
