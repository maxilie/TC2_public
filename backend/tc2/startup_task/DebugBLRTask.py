from datetime import date, datetime, timedelta
from random import random
from statistics import mean, median, stdev

from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.env.ExecEnv import ExecEnv
from tc2.startup_task.AbstractStartupTask import AbstractStartupTask
from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.stock_analysis.analysis_structs.BoundedLinearRegression import BoundedLinearRegressions
from tc2.stock_analysis.strategy_models.long_short_strategy.LSFavorModel import LSFavorModel
from tc2.stock_analysis.strategy_models.long_short_strategy.OscillationModel import OscillationModel
from tc2.util.TimeInterval import ContinuousTimeInterval
from tc2.util.candle_util import candles_in_period
from tc2.util.market_util import CLOSE_TIME, OPEN_TIME


class DebugBLRTask(AbstractStartupTask):
    """
    STARTUP TASK (single-run): Test what profit the LongShortStrategy generates given constant
     oscillation threshold of 20% and various signal strength thresholds of
     BoundedLinearRegression.
    """

    def run(self) -> None:
        # Clone live environment, connecting this thread to real data.
        live_env = ExecEnv(self.program.logfeed_optimization, self.program.logfeed_optimization, self.program.live_env)
        live_env.fork_new_thread()

        # Experiment settings.
        MAX_TRIALS_PER_DAY = 250  # max number of periods to evaluate per historical day
        EVAL_PERIOD_LEN = 3 * 60  # number of seconds over which to track profits
        EVAL_FLOOR_PERIOD_LEN = 7 * 60  # number of seconds over which to track killswitch floor

        # Load dates on which we have all the needed data.
        experiment_start_date = date(2018, 6, 1)
        spy_dates = live_env.mongo().get_dates_on_file(symbol='SPY',
                                                       start_date=experiment_start_date,
                                                       end_date=live_env.time().now().date())
        spxl_dates = live_env.mongo().get_dates_on_file(symbol='SPXL',
                                                        start_date=experiment_start_date,
                                                        end_date=live_env.time().now().date())
        spxl_dates = [day_date for day_date in spxl_dates if day_date in spy_dates]  # narrow spxl to spy dates
        spy_dates = [day_date for day_date in spy_dates if day_date in spxl_dates]  # narrow spy to spxl dates
        spxs_dates = live_env.mongo().get_dates_on_file(symbol='SPXS',
                                                        start_date=experiment_start_date,
                                                        end_date=live_env.time().now().date())
        spxs_dates = [day_date for day_date in spxs_dates if day_date in spy_dates]  # narrow spxs to spy=sxpl dates
        spy_dates = [day_date for day_date in spy_dates if day_date in spxs_dates]  # narrow spy to spxs<=sxpl dates
        spxl_dates = [day_date for day_date in spxl_dates if day_date in spy_dates]  # narrow spxl to spy<=sxpl dates
        assert len(spy_dates) == len(spxl_dates) == len(spxs_dates)

        # Init statistics on the experiment.
        spxl_blr_setup_vals = []
        spxs_blr_setup_vals = []
        spxl_blr_10_vals = []
        spxs_blr_10_vals = []
        spxl_blr_25_vals = []
        spxs_blr_25_vals = []
        spxl_profits = []
        spxl_floors = []
        spxs_profits = []
        spxs_floors = []
        oscillation_model = OscillationModel(live_env, AnalysisModelType.OSCILLATION)
        trend_model = LSFavorModel(live_env, AnalysisModelType.LS_FAVOR)

        # Simulate the days on which SPY, SPXL, and SPXS jointly have data.
        live_env.info_process(f'Beginning BLR simulations over {len(spxs_dates)} dates')
        for day_date in spxs_dates:
            # Load data for experiment.
            live_env.info_process(f'Running trials on {day_date:%m-%d-%Y} (successful trials: {len(spxl_profits)})')
            spy_data = live_env.mongo().load_symbol_day(symbol='SPY',
                                                        day=day_date)
            spxl_data = live_env.mongo().load_symbol_day(symbol='SPXL',
                                                         day=day_date)
            spxs_data = live_env.mongo().load_symbol_day(symbol='SPXS',
                                                         day=day_date)

            # Validate data.
            data_is_valid = True
            for day_data in [spy_data, spxl_data, spxs_data]:
                if not SymbolDay.validate_candles(day_data.candles):
                    data_is_valid = False
                    break
            if not data_is_valid:
                live_env.info_process(f'Invalid data on {day_date:%m-%d-%Y}')
                continue

            # Init time windows variables.
            start_moment = datetime.combine(day_date, OPEN_TIME) + timedelta(seconds=int(30 * 60))
            end_moment = datetime.combine(day_date, CLOSE_TIME) - timedelta(seconds=int(EVAL_PERIOD_LEN + 15 * 60))

            # Go thru time windows on each day.
            day_trials = 0
            while start_moment < end_moment and day_trials < MAX_TRIALS_PER_DAY:

                try:
                    # Move to the next time window.
                    start_moment += timedelta(seconds=random.randint(30, 120))
                    blr_setup_period = ContinuousTimeInterval((start_moment - timedelta(seconds=3 * 60)).time(),
                                                              start_moment.time())
                    blr_10_period = ContinuousTimeInterval((start_moment - timedelta(seconds=10 * 60)).time(),
                                                           start_moment.time())
                    blr_25_period = ContinuousTimeInterval((start_moment - timedelta(seconds=25 * 60)).time(),
                                                           start_moment.time())
                    eval_period = ContinuousTimeInterval(start_moment.time(),
                                                         (start_moment + timedelta(seconds=EVAL_PERIOD_LEN)).time())
                    eval_floor_period = ContinuousTimeInterval(
                        start_moment.time(), (start_moment + timedelta(seconds=EVAL_FLOOR_PERIOD_LEN)).time())

                    # Ignore non-oscillatory periods.
                    oscillation_val = oscillation_model.get_oscillation_val(
                        candles_in_period(blr_setup_period, spy_data.candles, spy_data.day_date))
                    if oscillation_val < 0.6:
                        continue

                    # Calculate BLR trendline indicators.
                    spxl_blr_setup_val = trend_model.get_blr_strength(BoundedLinearRegressions(
                        candles_in_period(blr_setup_period, spxl_data.candles, spxl_data.day_date)))
                    spxs_blr_setup_val = trend_model.get_blr_strength(BoundedLinearRegressions(
                        candles_in_period(blr_setup_period, spxs_data.candles, spxs_data.day_date)))
                    spxl_blr_10_val = trend_model.get_blr_strength(BoundedLinearRegressions(
                        candles_in_period(blr_10_period, spxl_data.candles, spxl_data.day_date)))
                    spxs_blr_10_val = trend_model.get_blr_strength(BoundedLinearRegressions(
                        candles_in_period(blr_10_period, spxs_data.candles, spxs_data.day_date)))
                    spxl_blr_25_val = trend_model.get_blr_strength(BoundedLinearRegressions(
                        candles_in_period(blr_25_period, spxl_data.candles, spxl_data.day_date)))
                    spxs_blr_25_val = trend_model.get_blr_strength(BoundedLinearRegressions(
                        candles_in_period(blr_25_period, spxs_data.candles, spxs_data.day_date)))

                    # Calculate maximum profits during evaluation period.
                    spxl_buy_price = candles_in_period(blr_setup_period, spxl_data.candles, spxl_data.day_date)[
                        -1].close
                    spxs_buy_price = candles_in_period(blr_setup_period, spxs_data.candles, spxs_data.day_date)[
                        -1].close
                    spxl_eval_candles = candles_in_period(eval_period, spxl_data.candles, spxl_data.day_date)
                    spxs_eval_candles = candles_in_period(eval_period, spxs_data.candles, spxs_data.day_date)
                    spxl_eval_floor_candles = candles_in_period(eval_floor_period, spxl_data.candles,
                                                                spxl_data.day_date)
                    spxs_eval_floor_candles = candles_in_period(eval_floor_period, spxs_data.candles,
                                                                spxs_data.day_date)
                    spxl_profit_pct = (max([candle.high * 0.3 + candle.open * 0.7 for candle in spxl_eval_candles]) -
                                       spxl_buy_price) / spxl_buy_price
                    spxs_profit_pct = (max([candle.high * 0.3 + candle.open * 0.7 for candle in spxs_eval_candles]) -
                                       spxs_buy_price) / spxs_buy_price
                    spxl_floor_pct = (spxl_buy_price -
                                      min([candle.low * 0.3 + candle.open * 0.7 for candle in
                                           spxl_eval_floor_candles])) / spxl_buy_price
                    spxs_floor_pct = (spxs_buy_price -
                                      min([candle.low * 0.3 + candle.open * 0.7 for candle in
                                           spxs_eval_floor_candles])) / spxs_buy_price

                    # Record trial stats.
                    spxl_blr_setup_vals.append(spxl_blr_setup_val)
                    spxs_blr_setup_vals.append(spxs_blr_setup_val)
                    spxl_blr_10_vals.append(spxl_blr_10_val)
                    spxs_blr_10_vals.append(spxs_blr_10_val)
                    spxl_blr_25_vals.append(spxl_blr_25_val)
                    spxs_blr_25_vals.append(spxs_blr_25_val)
                    spxl_profits.append(spxl_profit_pct)
                    spxl_floors.append(spxl_floor_pct)
                    spxs_profits.append(spxs_profit_pct)
                    spxs_floors.append(spxs_floor_pct)
                    day_trials += 1

                    # Print experiment stats every 100 trials.
                    if len(spxl_blr_setup_vals) > 0 and len(spxl_blr_setup_vals) % 100 != 0:
                        continue

                    live_env.info_process('\n\n')

                    def print_immediate_profit(val_lists, profits_list, threshold, symbol, trend_name):
                        # Get indices corresponding to vals that are above all thresholds.
                        indices = [i for i in range(len(val_lists[0]))]
                        for j in range(len(val_lists)):
                            indices = [i for i in indices if val_lists[j][i] >= threshold]

                        if len(indices) > 3:
                            profits = [profits_list[i] for i in indices]
                            profit_mean, profit_med, profit_stdev = (mean(profits), median(profits), stdev(profits))
                            immediate_profit = profit_med
                            live_env.info_process(
                                f'Immediate {symbol} profit (< 3 mins) when {trend_name} strength >= '
                                f'{100 * threshold}%: '
                                f'{100 * immediate_profit:.2f}% (n={len(profits)})')

                    def print_profit_ratio(val_lists, spxl_profits_list, spxs_profits_list, threshold, trend_name):
                        # Get indices corresponding to vals that are above all thresholds.
                        indices = [i for i in range(len(val_lists[0]))]
                        for j in range(len(val_lists)):
                            indices = [i for i in indices if val_lists[j][i] >= threshold]

                        if len(indices) > 3:
                            profit_ratios = [spxl_profits_list[i] / max(0.0002, spxs_profits_list[i]) for i in indices]
                            ratios_mean, ratios_med, ratios_stdev = (mean(profit_ratios), median(profit_ratios),
                                                                     stdev(profit_ratios))
                            live_env.info_process(
                                f'Immediate profit ratio (SPXL:SPXS) when {trend_name} strength >= '
                                f'{100 * threshold}%: '
                                f'{ratios_med:.2f}:1 (n={len(profit_ratios)})')

                    # TODO NEXT: Implement a -1.65% killswitch in the strategy.

                    # TODO NEXT: What pct of oscillation range is expected profit?

                    def print_killswitch_floor(val_lists, floors_list, threshold, symbol, trend_name):
                        # Get indices corresponding to vals that are above all thresholds.
                        indices = [i for i in range(len(val_lists[0]))]
                        for j in range(len(val_lists)):
                            indices = [i for i in indices if val_lists[j][i] >= threshold]

                        if len(indices) > 3:
                            floors = [-floors_list[i] for i in indices]
                            floor_mean, floor_med, floor_stdev = (mean(floors), median(floors), stdev(floors))
                            killswitch_floor = floor_med - 1.5 * floor_stdev
                            live_env.info_process(
                                f'{symbol} killswitch activation (-1.5 stdev floor) when {trend_name} strength >= '
                                f'{100 * threshold}%: '
                                f'{100 * killswitch_floor:.2f}% (n={len(floors)})')

                    """
                    # Print immediate profits when BLR strength >= 70%.
                    print_immediate_profit([spxl_blr_6_vals], spxl_profits, 0.7, 'SPXL', 'BLR-6')
                    print_immediate_profit([spxs_blr_6_vals], spxs_profits, 0.7, 'SPXS', 'BLR-6')
                    print_immediate_profit([spxl_blr_10_vals], spxl_profits, 0.7, 'SPXL', 'BLR-10')
                    print_immediate_profit([spxs_blr_10_vals], spxs_profits, 0.7, 'SPXS', 'BLR-10')
                    print_immediate_profit([spxl_blr_25_vals], spxl_profits, 0.7, 'SPXL', 'BLR-25')
                    print_immediate_profit([spxs_blr_25_vals], spxs_profits, 0.7, 'SPXS', 'BLR-25')

                    # Print immediate profits when BLR strength >= 85%.
                    print_immediate_profit([spxl_blr_6_vals], spxl_profits, 0.85, 'SPXL', 'BLR-6')
                    print_immediate_profit([spxs_blr_6_vals], spxs_profits, 0.85, 'SPXS', 'BLR-6')
                    print_immediate_profit([spxl_blr_10_vals], spxl_profits, 0.85, 'SPXL', 'BLR-10')
                    print_immediate_profit([spxs_blr_10_vals], spxs_profits, 0.85, 'SPXS', 'BLR-10')
                    print_immediate_profit([spxl_blr_25_vals], spxl_profits, 0.85, 'SPXL', 'BLR-25')
                    print_immediate_profit([spxs_blr_25_vals], spxs_profits, 0.85, 'SPXS', 'BLR-25')

                    # Print immediate profits when BLR strength >= 95%.
                    print_immediate_profit([spxl_blr_6_vals], spxl_profits, 0.95, 'SPXL', 'BLR-6')
                    print_immediate_profit([spxs_blr_6_vals], spxs_profits, 0.95, 'SPXS', 'BLR-6')
                    print_immediate_profit([spxl_blr_10_vals], spxl_profits, 0.95, 'SPXL', 'BLR-10')
                    print_immediate_profit([spxs_blr_10_vals], spxs_profits, 0.95, 'SPXS', 'BLR-10')
                    print_immediate_profit([spxl_blr_25_vals], spxl_profits, 0.95, 'SPXL', 'BLR-25')
                    print_immediate_profit([spxs_blr_25_vals], spxs_profits, 0.95, 'SPXS', 'BLR-25')

                    # Print SPXL immediate profit when second 2 BLR strengths >= 90%.
                    print_immediate_profit([spxl_blr_10_vals, spxl_blr_25_vals], spxl_profits,
                                           0.9, 'SPXL', 'BLR-10-25')

                    # Print SPXL immediate profit when all BLR strengths >= 30%.
                    print_immediate_profit([spxl_blr_6_vals, spxl_blr_10_vals, spxl_blr_25_vals], spxl_profits,
                                           0.3, 'SPXL', 'BLR-6-10-25')
                    """

                    # Print SPXL:SPXS profit ratio when BLR strength >= 60%.
                    print_profit_ratio([spxl_blr_setup_vals], spxl_profits, spxs_profits, 0.6, 'BLR-3')
                    print_profit_ratio([spxl_blr_10_vals], spxl_profits, spxs_profits, 0.6, 'BLR-10')
                    print_profit_ratio([spxl_blr_25_vals], spxl_profits, spxs_profits, 0.6, 'BLR-25')

                    # Print SPXL:SPXS profit ratio when BLR strength >= 85%.
                    print_profit_ratio([spxl_blr_setup_vals], spxl_profits, spxs_profits, 0.85, 'BLR-3')
                    print_profit_ratio([spxl_blr_10_vals], spxl_profits, spxs_profits, 0.85, 'BLR-10')
                    print_profit_ratio([spxl_blr_25_vals], spxl_profits, spxs_profits, 0.85, 'BLR-25')

                    # Print SPXL:SPXS profit ratio when BLR strength >= 95%.
                    print_profit_ratio([spxl_blr_setup_vals], spxl_profits, spxs_profits, 0.95, 'BLR-3')
                    print_profit_ratio([spxl_blr_10_vals], spxl_profits, spxs_profits, 0.95, 'BLR-10')
                    print_profit_ratio([spxl_blr_25_vals], spxl_profits, spxs_profits, 0.95, 'BLR-25')

                    # Print SPXL:SPXS profit ratio when long BLR strengths >= 60%.
                    print_profit_ratio([spxl_blr_10_vals, spxl_blr_25_vals],
                                       spxl_profits, spxs_profits, 0.6, 'BLR-10-25')

                    # Print expected min profit when osc_val >= 60%.
                    print_immediate_profit([spxl_blr_setup_vals],
                                           [min(spxl_profits[i], spxs_profits[i]) for i in range(len(spxl_profits))],
                                           0, '', 'oscillating... N/A')

                    # Print killswitch floor when osc_val >= 60%.
                    print_killswitch_floor([spxl_blr_setup_vals],
                                           [max(spxl_floors[i], spxs_floors[i]) for i in range(len(spxl_floors))],
                                           0, '', 'oscillating... N/A')

                except Exception as e:
                    # live_env.warn_process(f'BLR Experiment error: {traceback.format_exc()}')
                    continue
