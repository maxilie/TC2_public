import json
import os
import traceback
from datetime import date, timedelta

from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.data.stock_data_collection.PolygonDataCollector import PolygonDataCollector
from tc2.env.ExecEnv import ExecEnv
from tc2.startup_task.AbstractStartupTask import AbstractStartupTask


class DumpAIDataTask(AbstractStartupTask):
    """
    STARTUP TASK (single-run): Dump all S&P-500 data into a txt file.
    """

    def run(self) -> None:
        # Set data parameters.
        start_date = date(year=2002, month=1, day=1)
        end_date = self.program.live_env.time().now().today() - timedelta(days=1)

        # Clone live environment so it can run on this thread.
        live_env = ExecEnv(self.program.logfeed_program, self.program.logfeed_program, self.program.live_env)
        live_env.fork_new_thread()
        data_collector = PolygonDataCollector(self.program.logfeed_program, self.program.logfeed_program, live_env.time())

        # Clear the data file.
        filename = 'debug_data/spy_ai_data.txt'
        try:
            if not os.path.exists('debug_data'):
                os.mkdir('debug_data')
            with open(filename, 'w+') as file:
                file.write('')
            os.remove(filename)
        except Exception as e:
            print(f'Error deleting file: "{filename}"')
            pass

        # Go through the data we have on file.
        day_date = start_date - timedelta(days=1)
        while day_date < end_date:

            # Get the next market day.
            day_date = self.program.live_env.time().get_next_mkt_day(day_date)

            # Load price data.
            print(f'Fetching SPY data for {day_date:%m-%d-%Y}')
            day_data = live_env.mongo().load_symbol_day('SPY', day_date)

            # Get fresh data from polygon.io, if necessary.
            if not SymbolDay.validate_candles(day_data.candles):
                try:
                    day_data = data_collector.collect_candles_for_day(day_date, 'SPY')
                except Exception as e:
                    live_env.error_process('Error collecting polygon-rest data:')
                    live_env.warn_process(traceback.format_exc())

            # Validate the data.
            if day_data is None or not SymbolDay.validate_candles(day_data.candles):
                print(F'COULD NOT COMPILE PRICE DATA FOR SPY ON {day_date:%m-%d-%Y}')
                continue

            # Convert candles into sentences.


            #

            # Convert the data into json.
            data_dict = day_data.to_json()

            # Append the data to the txt file.
            with open(f'debug_data/spy_ai_data.txt', 'a+') as f:
                f.write(json.dumps(data_dict))

        print(f'Dumped data to TC2_data/{filename}')
