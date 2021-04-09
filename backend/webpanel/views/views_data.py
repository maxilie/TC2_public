import json
import time as pytime
import traceback
from datetime import datetime, timedelta, date
from threading import Thread
from typing import List

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from webpanel import shared, api_util

"""
Contains methods to handle api requests on the /api/data endpoint.
These methods are for controlling data collection.
"""


@api_view(['GET'])
def get_data_status(request):
    """Returns the status of the program's data collection activities."""
    from tc2.TC2Program import TC2Program

    # Fetch the program instance
    program: TC2Program = shared.program

    # Fork the live environment for the API worker thread
    env = api_util.fork_live_env(program.logfeed_data)

    # Ensure data is not already being collected
    if shared.data_busy.value or not env.is_data_loaded():
        return Response('Busy')
    else:
        return Response('Not in use')


@api_view(['GET'])
def is_patching(request):
    """
    Returns whether data is being patched.
    """
    return Response('true') if shared.patching_data.value else Response('false')


@api_view(['GET'])
def patch_data(request):
    """
    Starts data patching off-thread for the given symbol starting at the given start date.
    """
    from tc2.TC2Program import TC2Program
    from tc2.util.data_constants import START_DATE

    try:

        # Parse start_date parameter
        start_date = api_util.parse_param_date(request, 'start_date')
        if start_date is None or start_date < START_DATE:
            return Response('Parameter "start_date" missing or invalid',
                            status=status.HTTP_400_BAD_REQUEST)

        # Parse symbols parameter
        symbols = api_util.parse_param_str_list(request, 'symbols')
        if symbols is None:
            return Response('Parameter "symbols" missing or invalid',
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            symbols = [symbol.strip().upper() for symbol in symbols]
    except Exception as e:
        api_util.log_stacktrace('parsing parameters from data patch request', traceback.format_exc())
        return Response('Error parsing parameters',
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Fetch the program instance
    program: TC2Program = shared.program

    # Fork the live environment for the API worker thread
    env = api_util.fork_live_env(program.logfeed_data)

    # Ensure data is not already being manipulated
    if shared.data_busy.value or not env.is_data_loaded():
        return Response('Already busy manipulating data',
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Check for missing data in another thread
    env.mark_data_as_busy()
    shared.data_busy.value = True
    shared.patching_data.value = True
    try:
        def patch_logic():
            # Fork the live environment so it can run in this thread
            env = api_util.fork_live_env(program.logfeed_data)
            _patch_data(env, start_date, symbols)
            env.mark_data_as_loaded()
            shared.data_busy.value = False
            shared.patching_data.value = False

        patch_thread = Thread(target=patch_logic)
        patch_thread.start()

        return Response(f'Patch process started...')
    except Exception:
        env.mark_data_as_loaded()
        shared.data_busy.value = False
        shared.patching_data.value = False
        api_util.log_stacktrace('patching data', traceback.format_exc())
        return Response('Error patching data!',
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def is_healing(request):
    """
    Returns whether data is being healed.
    """
    return Response('true') if shared.healing_data.value else Response('false')


@api_view(['GET'])
def heal_data(request):
    """
    Starts a heal data process off-thread.
    """

    # Fork the live environment for the API worker thread
    env = api_util.fork_live_env(shared.program.logfeed_data)

    # Ensure data is not already being collected
    if shared.data_busy.value or not env.is_data_loaded():
        return Response('Already busy collecting data',
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Mark data as busy while healing it in a separate thread
    env.mark_data_as_busy()
    shared.data_busy.value = True
    shared.healing_data.value = True

    def heal_logic():
        # Fork the execution environment so it can run on this thread
        env = api_util.fork_live_env(shared.program.logfeed_data)
        try:
            # Heal data
            _heal_data(env)
            env.mark_data_as_loaded()
            shared.data_busy.value = False
            shared.healing_data.value = False
        except Exception as e:
            env.mark_data_as_loaded()
            shared.data_busy.value = False
            shared.healing_data.value = False
            env.error_process(f'Error healing data:')
            env.warn_process(traceback.format_exc())

    data_heal_thread = Thread(target=heal_logic)
    data_heal_thread.start()

    return Response('Started data healing task in another thread')


@api_view(['GET'])
def reset_trade_history(request):
    """
    Removes all trade and strategy run history from the Redis database.
    """
    from tc2.TC2Program import TC2Program
    from tc2.util.strategy_constants import DAY_STRATEGY_IDS

    # Fetch the program instance
    program: TC2Program = shared.program

    # Reset Redis entries
    try:
        def trade_reset_logic():
            # Fork the execution environment so it can run on this thread
            env = api_util.fork_live_env(program.logfeed_data)

            # Remove trade history from redis
            env.redis().clear_trade_history()
            env.redis().clear_run_history(strategy_ids=DAY_STRATEGY_IDS)

        trade_reset_thread = Thread(target=trade_reset_logic)
        trade_reset_thread.start()

        return Response('Trade and strategy history data removed from Redis')
    except Exception:
        api_util.log_stacktrace('resetting trade history', traceback.format_exc())
        return Response('Error resetting trade history!')


@api_view(['GET'])
def get_symbols(request):
    """
    Returns a list of the symbols being traded.
    """
    from tc2.env.Settings import Settings

    # Fetch symbols from the program
    try:
        # Fork the execution environment so it can run on this thread
        env = api_util.fork_live_env(shared.program.logfeed_data)

        return Response(Settings.get_symbols(env))
    except Exception:
        api_util.log_stacktrace('fetching symbols', traceback.format_exc())
        return Response('Error fetching symbols!')


@api_view(['GET'])
def get_dates(request, symbol: str):
    """
    Returns a list of dates for which the program has data on the symbol.
    """

    # Fetch the program instance
    from tc2.TC2Program import TC2Program
    program: TC2Program = shared.program

    # Fetch dates from the program
    try:
        # Fork the execution environment so it can run on this thread
        env = api_util.fork_live_env(logfeed_process=program.logfeed_api)

        # Return dates for we have data on the symbol
        from tc2.util.date_util import DATE_FORMAT
        from tc2.util.data_constants import START_DATE
        dates = [day_date.strftime(DATE_FORMAT) for day_date in
                 env.mongo().get_dates_on_file(symbol, START_DATE, env.time().now().date())]

        return Response(dates)
    except Exception:
        api_util.log_stacktrace('fetching symbol dates', traceback.format_exc())
        return Response('Error fetching symbol dates!')


@api_view(['GET'])
def get_warmup_day_options(request):
    """
    Returns a list of [0, 1, ..., n] days, up to the number of dates for which we have continuous data on the symbol.
    """
    from tc2.util.data_constants import START_DATE

    # Decode parameters
    symbol = api_util.parse_param_str(request, 'symbol')
    day_date = api_util.parse_param_date(request, 'date')

    # Validate parameters
    if symbol is None or day_date is None:
        return Response('You must specify valid symbol and date', status=status.HTTP_400_BAD_REQUEST)

    # Calculate the number of continuous days preceding day_date
    try:
        # Fork the execution environment so it can run on this thread
        env = api_util.fork_live_env()

        # Load all dates on file
        all_dates = env.mongo().get_dates_on_file(symbol=symbol,
                                                  start_date=START_DATE,
                                                  end_date=day_date)

        # Find out how many consecutive dates on file directly precede day_date
        continuous_dates = 0
        preceding_date = env.time().get_prev_mkt_day(day_date)
        if preceding_date not in all_dates:
            return Response([0])
        for i in range(9999):
            # Go back one market day
            preceding_date = env.time().get_prev_mkt_day(preceding_date)
            # Stop when a data discontinuity is found
            if preceding_date not in all_dates:
                break
            # Increment
            else:
                continuous_dates += 1

        # Return a list containing every number between 0 and continuous_dates
        return Response([i for i in range(continuous_dates + 1)])
    except Exception:
        api_util.log_stacktrace('fetching warmup day options', traceback.format_exc())
        return Response('Error fetching warmup day options!')


@api_view(['GET'])
def get_simulation_output(request):
    """
    Returns a json object containing the output of the last simulation.
    """

    try:
        # Fork the execution environment so it can run on this thread.
        live_env = api_util.fork_live_env()

        # Fetch the last simulation output from redis.
        sim_output = live_env.redis().get_simulation_output()
        sim_output_str = '' if sim_output is None else json.dumps(sim_output)

        # Return the simulation output as a string.
        return Response(sim_output_str)
    except Exception:
        api_util.log_stacktrace('fetching simulation output', traceback.format_exc())
        return Response('Error fetching simulation output!')


@api_view(['GET'])
def reset_collection_attempts(request):
    """
    Resets the record of failed attempts at data collection for all symbols.
    Doing so allows future data healing tasks to try collecting again.
    """
    from tc2.TC2Program import TC2Program

    try:
        # Fetch the program instance
        program: TC2Program = shared.program

        # Fork the live environment for the API worker thread
        env = api_util.fork_live_env(program.logfeed_data)

        # Reset the record
        env.redis().reset_day_difficulties()

        return Response(f'Data collection attempt record reset')
    except Exception:
        api_util.log_stacktrace('resetting data collection attempt record', traceback.format_exc())
        return Response('Error resetting data collection attempt record!',
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _patch_data(env: 'ExecEnv',
                start_date: date,
                symbols: List[str]) -> None:
    """
    Returns to the given start date and fills in missing data.
    Resets and retrains analysis models when new data is found, but does not delete price data.
    """
    from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
    from tc2.data.stock_data_collection.ModelFeeder import ModelFeeder
    model_feeder = ModelFeeder(env)

    # Log this patching process
    stop_date = env.time().get_prev_mkt_day(datetime.now().date())
    day_date = env.time().get_prev_mkt_day(start_date)
    env.info_process(f'Patching data for {symbols} from {day_date} to {stop_date}')

    # Check each day between start and stop dates
    while day_date < stop_date:

        # Move to the next market date
        day_date = env.time().get_next_mkt_day(day_date)
        start_moment = pytime.monotonic()

        # Patch each symbol on day_date
        for symbol in symbols:

            # Skip if the symbol already has valid data
            day_data = env.mongo().load_symbol_day(symbol, day_date)
            if SymbolDay.validate_candles(day_data.candles):
                continue

            # Collect polygon-rest data
            try:
                day_data = env.data_collector().collect_candles_for_day(day_date, symbol)
            except Exception as e:
                api_util.log_stacktrace('collecting polygon-rest data', traceback.format_exc())

            # Validate data
            if day_data is not None and SymbolDay.validate_candles(day_data.candles):
                # Save data
                env.mongo().save_symbol_day(day_data)

                # Use data to train models for symbol on day
                model_feeder.train_models(symbol=symbol,
                                          day_date=day_date,
                                          day_data=day_data,
                                          stable=True)
            else:
                env.warn_process(f'Couldn\'t collect patch data for {symbol} on {day_date}: '
                                 f'{"null" if day_date is None else len(day_data.candles)} candles')
        env.info_process(f'Patching for symbol(s) on {day_date} took {pytime.monotonic() - start_moment:.1f}s')


def _heal_data(env: 'ExecEnv') -> None:
    """
    Intelligently patches price data and analysis models quickly.
    Logs potential data issues to the data log feed.
    """
    from tc2.util.data_constants import START_DATE
    from tc2.env.Settings import Settings
    from tc2.util.date_util import DATE_FORMAT
    from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
    from tc2.data.stock_data_collection.ModelFeeder import ModelFeeder

    env.info_process('Data healing process started')

    # Create a ModelFeeder
    model_feeder = ModelFeeder(env)

    # Get a list of all market dates START_DATE thru yesterday
    market_dates = []
    latest_date = START_DATE - timedelta(days=1)
    while latest_date < env.time().get_prev_mkt_day(env.time().now().date()):
        latest_date = env.time().get_next_mkt_day(latest_date)
        market_dates.append(latest_date)

    # Heal each symbol
    for symbol in Settings.get_symbols(env):
        # Find the latest date after which all days have day_difficulty <= 1
        continuous_start_index = len(market_dates) - 1
        for i in range(len(market_dates) - 1, 0, -1):
            if env.redis().get_day_difficulty(symbol, market_dates[i]) <= 1:
                continuous_start_index = i
                continue
            break

        # Get mongo dates
        dates_on_file = env.mongo().get_dates_on_file(symbol, market_dates[continuous_start_index],
                                                      env.time().now().date())

        env.info_process(
            f'Healing {symbol}\'s recent data since {market_dates[continuous_start_index].strftime(DATE_FORMAT)}')
        for i in range(continuous_start_index, len(market_dates)):

            # Load the price data we already have
            day_date = market_dates[i]
            day_data = env.mongo().load_symbol_day(symbol, day_date)

            # Try to re-collect if we don't have data on file for day_date
            if day_date not in dates_on_file or not SymbolDay.validate_candles(day_data.candles):

                # Re-collect the day's data
                try:
                    day_data = env.data_collector().collect_candles_for_day(day_date, symbol)
                except Exception as e:
                    api_util.log_stacktrace('collecting polygon-rest data', traceback.format_exc())

                # Validate the data
                if SymbolDay.validate_candles(day_data.candles):
                    # Save the valid data
                    env.redis().reset_day_difficulty(symbol, day_date)
                    env.mongo().save_symbol_day(day_data)

                else:
                    # Mark failed data collection attempt
                    continuous_start_index = i
                    env.redis().incr_day_difficulty(symbol, day_date)
                    env.info_process(f'Failed to collect {symbol}\'s data on {day_date.strftime(DATE_FORMAT)} '
                                     f'(failed attempt #{env.redis().get_day_difficulty(symbol, day_date)})')
                    continue

            # Make sure that all models have been trained on this data
            model_feeder.train_models(symbol=symbol,
                                      day_date=day_date,
                                      day_data=day_data,
                                      stable=True,
                                      possibly_already_trained=True)

        # Log the dates on which the symbol's models are trained
        env.info_process(f'{symbol}\'s models are now trained starting from '
                         f'{market_dates[continuous_start_index].strftime(DATE_FORMAT)}')
