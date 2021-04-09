import json
import os
import traceback
from datetime import date, timedelta

from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.data.stock_data_collection.PolygonDataCollector import PolygonDataCollector
from tc2.env.ExecEnv import ExecEnv
from tc2.startup_task.AbstractStartupTask import AbstractStartupTask


class DumpSPDataTask(AbstractStartupTask):
    """
    STARTUP TASK (single-run): Dump SymbolDay objects for S&P symbols into text files.
    """

    def run(self) -> None:
        # Set symbol and date we need data for.
        symbols = ['SPY', 'SPXL', 'SPXS']
        start_date = date(year=2020, month=4, day=1)
        days_to_dump = 5

        # Clone live environment so it can run on this thread.
        live_env = ExecEnv(self.program.logfeed_program, self.program.logfeed_program, self.program.live_env)
        live_env.fork_new_thread()
        data_collector = PolygonDataCollector(self.program.logfeed_program, self.program.logfeed_program, live_env.time())

        # Go through each symbol.
        for symbol in symbols:

            # Go through the first 5 market days starting with start_date.
            day_date = start_date - timedelta(days=1)
            for i in range(days_to_dump):

                # Get the next market day.
                day_date = live_env.time().get_next_mkt_day(day_date)

                # Load price data.
                print(f'Fetching {symbol} data for {day_date:%m-%d-%Y}')
                day_data = live_env.mongo().load_symbol_day(symbol, day_date)

                # Get fresh data from polygon.io, if necessary.
                if not SymbolDay.validate_candles(day_data.candles):
                    try:
                        day_data = data_collector.collect_candles_for_day(day_date, symbol)
                    except Exception as e:
                        live_env.error_process('Error collecting polygon-rest data:')
                        live_env.warn_process(traceback.format_exc())

                # Validate the data.
                if day_data is None or not SymbolDay.validate_candles(day_data.candles):
                    print(F'COULD NOT COMPILE DEBUG PRICE DATA FOR {symbol} ON {day_date:%m-%d-%Y}')
                    continue

                # Convert the data into json.
                data_dict = day_data.to_json()

                # Dump the data into a text file.
                if not os.path.exists('debug_data'):
                    os.mkdir('debug_data')
                with open(f'debug_data/{symbol}_{day_date:%m-%d-%Y}.txt', 'w+') as f:
                    f.write(json.dumps(data_dict))
                print(f'Dumped data to TC2_data/debug_data/{symbol}_{day_date:%m-%d-%Y}')
