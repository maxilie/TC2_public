from datetime import date, timedelta
from typing import Optional, List

from tc2.env.EnvType import EnvType
from tc2.data.data_storage.mongo.workers.AbstractMongoWorker import AbstractMongoWorker
from tc2.util.data_constants import START_DATE
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.data.data_structs.price_data.DailyCandle import DailyCandle
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.util.date_util import date_to_datetime, datetime_to_date, DATE_FORMAT
from tc2.util.synchronization import synchronized_on_mongo


class MongoPriceWorker(AbstractMongoWorker):
    """
    Contains functionality for saving and loading stock market price data.
    """

    def get_dates_on_file(self, symbol: str, start_date: date, end_date: date,
                          debug_output: Optional[List[str]] = None) -> List[date]:
        """Returns a list of date objects for which we have data for the symbol."""
        query = {"symbol": symbol}
        requested_fields = {"date": 1}
        if debug_output is not None:
            debug_output.append('querying mongo dates on file for {}'.format(symbol))
        responses = self.candle_collection_secondly.find(query, requested_fields)
        if responses is None:
            if debug_output is not None:
                debug_output.append('no mongo dates on file for {}'.format(symbol))
            return []
        dates = []
        start_datetime = date_to_datetime(start_date)
        end_datetime = date_to_datetime(end_date)
        for doc in responses:
            if start_datetime <= doc['date'] <= end_datetime:
                dates.append(datetime_to_date(doc['date']))
        dates.sort()
        if debug_output is not None:
            debug_output.append('mongo dates found: ' +
                                ', '.join([day_date.strftime(DATE_FORMAT) for day_date in dates]))
        return dates

    def load_symbol_day(self, symbol: str, day: date, debug_output: Optional[List[str]] = None) -> SymbolDay:
        """Queries MongoDB for a list of secondly candles for the day and puts them into a SymbolDay object."""
        candles = self._get_candles_for_day(symbol, day, debug_output)
        return SymbolDay(symbol, day, candles)

    @synchronized_on_mongo
    def load_aggregate_candle(self, symbol: str, day: date, debug_output: Optional[List[str]]) -> Optional[DailyCandle]:
        """Queries MongoDB for the day's aggregate candle, and puts it into a DailyCandle object."""
        query = {"symbol": symbol.upper(), "date": date_to_datetime(day)}
        requested_fields = {"candle": 1}
        response = self.candle_collection_daily.find_one(query, requested_fields)
        if debug_output is not None:
            debug_output.append('mongo._load_aggregate_candle received response for {} {}: {}'
                                .format(symbol, day.strftime(DATE_FORMAT), str(response)[0:200] + '...'))
        if response is None or 'candle' not in response or response['candle'] == '':
            return None
        else:
            return DailyCandle.from_str(response['candle'])

    def save_symbol_day(self, day_data: SymbolDay, debug_output: Optional[List[str]] = None) -> None:
        """
        Saves the day's data in MongoDB, or removes it if day_data.candles is empty.
        """

        # Make candle moments timezone-naive
        for candle in day_data.candles:
            candle.moment = candle.moment.replace(tzinfo=None)

        # Save candles

        if len(day_data.candles) == 0:

            # No data present: delete both secondly and daily data
            if debug_output is not None:
                debug_output.append('mongo.save_symbol_day: dropping the day since candles list is empty')
            self._drop_day_data(day_data.symbol, day_data.day_date, debug_output)

        else:

            # Data present: save secondly candles
            if debug_output is not None:
                debug_output.append('mongo.save_symbol_day: saving secondly candles for {} ({})'
                                    .format(day_data.symbol, len(day_data.candles)))
            self._update_secondly_candles(day_data, debug_output)

            # Data present: calculate and save daily candle
            if debug_output is not None:
                debug_output.append('mongo.save_symbol_day: saving daily candle for {}'.format(day_data.symbol))
            self._update_aggregate_candle(day_data.symbol, day_data.create_daily_candle(), debug_output)

    def remove_price_data_before(self, symbol: str, cutoff_date: date,
                                 debug_output: Optional[List[str]] = None) -> None:
        """Removes days from mongo before cutoff_date."""
        for day_date in self.get_dates_on_file(symbol=symbol, start_date=START_DATE,
                                               end_date=cutoff_date - timedelta(days=1)):
            if debug_output is not None:
                debug_output.append(
                    'mongo.remove_price_data_before dropping {}'.format(day_date.strftime(DATE_FORMAT)))
            self._drop_day_data(symbol, day_date, debug_output)

    def remove_price_data_after(self, symbol: str, cutoff_date: date, today: date,
                                debug_output: Optional[List[str]] = None) -> None:
        """Removes days from mongo after cutoff_date."""
        for day_date in self.get_dates_on_file(symbol=symbol, start_date=cutoff_date + timedelta(days=1),
                                               end_date=today):
            if debug_output is not None:
                debug_output.append('mongo.remove_price_days_after dropping {}'.format(day_date.strftime(DATE_FORMAT)))
            self._drop_day_data(symbol, day_date, debug_output)

    def drop_symbol(self, symbol: str) -> None:
        """Clears MongoDB of price and analysis/ai data on the symbol."""
        query = {"symbol": symbol}
        if self.env_type is EnvType.LIVE:
            self.error_main('dropping {} on all days'.format(symbol))
        self.candle_collection_secondly.delete_many(query)
        self.candle_collection_daily.delete_many(query)
        self.neural_collection.delete_many(query)

    def _get_candles_for_day(self, symbol: str, day: date, debug_output: Optional[List[str]] = None) -> List[Candle]:
        """
        Returns a list of Candles for the symbol on the date.
        This function is not synchronized because it is assumed the the outermost function calling it is synchronized.
        """
        query = {"symbol": symbol.upper(), "date": date_to_datetime(day)}
        requested_fields = {"candles": 1}
        response = self.candle_collection_secondly.find_one(query, requested_fields)
        if debug_output is not None:
            debug_output.append('mongo._get_candles_for_day received response for {} {}: {}'
                                .format(symbol, day.strftime(DATE_FORMAT), str(response)[0:200] + '...'))
        if response is None or response == {} or 'candles' not in response:
            if debug_output is not None:
                debug_output.append('mongo._get_candles_for_day returning empty list')
            return []
        candles = []
        for i, encoded_candle in enumerate(response['candles']):
            candles.append(Candle.from_str(encoded_candle))

        if debug_output is not None:
            debug_output.append('mongo._get_candles_for_day returning {} Candle objects'.format(len(candles)))
        return candles

    def _update_secondly_candles(self, day_data: SymbolDay, debug_output: Optional[List[str]] = None) -> None:
        """Inserts or replaces the given candles on the given date."""
        query = {"symbol": day_data.symbol, "date": date_to_datetime(day_data.day_date)}
        new_doc = {"symbol": day_data.symbol, "date": date_to_datetime(day_data.day_date),
                   'candles': [str(candle) for candle in day_data.candles]}
        self.candle_collection_secondly.replace_one(query, new_doc, upsert=True)

    def _update_aggregate_candle(self,
                                 symbol: str,
                                 day_data: DailyCandle,
                                 debug_output: Optional[List[str]] = None) -> None:
        """Inserts or replaces the given daily-resolution candle on the given date."""
        query = {"symbol": symbol.upper(), "date": date_to_datetime(day_data.day_date)}
        new_doc = {"symbol": symbol.upper(), "date": date_to_datetime(day_data.day_date),
                   "candle": str(day_data)}
        self.candle_collection_daily.replace_one(query, new_doc, upsert=True)

    def _drop_day_data(self,
                       symbol: str,
                       day: date,
                       debug_output: Optional[List[str]] = None) -> None:
        """
        Deletes a date (containing a list of candles) from mongo, including both second- and daily-resolution data.
        This function is not synchronized because it is assumed the the outermost function calling it is synchronized.
        """
        query = {"symbol": symbol.upper(), "date": date_to_datetime(day)}
        num_deleted = self.candle_collection_secondly.delete_many(query).deleted_count
        num_deleted += self.candle_collection_daily.delete_many(query).deleted_count
        if debug_output is not None:
            debug_output.append('mongo._drop_day_data dropped {} document(s) for {} on {}/{}/{}'
                                .format(num_deleted, symbol, day.month, day.day, day.year))
        if self.env_type is EnvType.LIVE:
            self.error_main(f'dropping {symbol} candles on {day:%m-%d-%Y}')
