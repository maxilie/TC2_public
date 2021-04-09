from datetime import timedelta, datetime
from statistics import stdev, median

from numpy import mean

from tc2.stock_analysis.AbstractSpotModel import AbstractSpotModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade, SymbolGradeValue
from tc2.stock_analysis.strategy_models.breakout1_strategy.Breakout1ModelOutput import Breakout1ModelOutput
from tc2.stock_analysis.strategy_models.breakout1_strategy.Breakout1ModelSteps import Breakout1ModelSteps
from tc2.stock_analysis.model_output.ModelStep import ModelStep
from tc2.stock_analysis.model_output.TrendLineFinder import TrendLineFinder
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.strategy.strategies.breakout1 import breakout1_constants
from tc2.util.TimeInterval import ContinuousTimeInterval
from tc2.util.candle_util import min_candle_in_period, max_candle_in_period, midpoint_candle_in_period, \
    aggregate_minute_candles, candles_in_period
from tc2.util.date_util import DATE_FORMAT
from tc2.util.math_util import ema


class Breakout1Model(AbstractSpotModel):
    """
    Validates pre-conditions for Breakout1Strategy:
        - Price dips to support toward the middle/end of the period
        - Price breaks resistance at the end of the period
        - Range decreases from [0, 0.3] to [0.31, 0.65]
        - Range decreases from [0.31, 0.65] to [0.66, 0.85]
        - Reward is not minimal (range at period's midpoint > 0.15% of symbol's price)
        - Risk is minimal: price usually does not drop when volume increases
        - Risk is minimal: no extra high price drops with extra high volume
        - Volume increases during this period more than it did during the same period on previous days

        TODO: Don't use candle low to construct sup_line (and high to construct res_line). Soften it using:
        TODO    0.3*candle.open = 0.7 * candle.low

    """

    OUTPUT_TYPE = Breakout1ModelOutput

    def calculate_output(self, symbol: str) -> OUTPUT_TYPE:
        """Creates a Breakout1ModelOutput for the symbol on this day."""

        # Create a Breakout1ModelOutput to hold the model's data as we perform checks on it
        output = Breakout1ModelOutput(self.time().now().date())

        # Create a time interval
        period_start = self.time().now() - timedelta(seconds=breakout1_constants.BREAKOUT_SETUP_MINS * 60)
        if not self._create_time_interval(output, period_start):
            return output

        # Load and validate the period's data
        if not self._load_period_data(output, symbol):
            return output

        # Find the period's lowest price
        output.period_low = min([candle.low for candle in output.period_data])

        # Calculate the period's price range
        output.period_range = max([candle.high for candle in output.period_data]) - \
                              min([candle.low for candle in output.period_data])

        # Draw a resistance line
        if not self._construct_res_line(output):
            return output

        # Draw a support line
        if not self._construct_sup_line(output):
            return output

        # Check that the price has recently dipped to the support line
        if not self._dips_to_support(output):
            return output

        # Check that the price has recently broken the resistance line
        if not self._breaks_resistance(output):
            return output

        # Check that the range decreases from [0, 0.31] to [0.31, 0.65]
        if not self._check_range_change_1(output):
            return output

        # Check that the range decreases from [0.31, 0.65] to [0.66, 0.85]
        if not self._check_range_change_2(output):
            return output

        # Check that the upper bound on our payoff isn't too low
        if not self._check_max_reward(output):
            return output

        # Check that the price doesn't drop too often when the minute's volume increases
        if not self._check_high_volume_drop_ratio(output):
            return output

        # Check that the strongest high-volume dip is not more than 1.7 standard deviations stronger
        # than the average minute's |high-low|
        if not self._check_strongest_high_volume_dip(output):
            return output

        # Check that this period's moving-average volume is higher than the 7-day median during the same period
        if not self._check_ema_volume_excitement(output):
            return output

        # Mark the symbol as viable since it passed all checks
        output.viability_status = SymbolGradeValue.PASS
        return output

    def grade_symbol(self, symbol: str, output: OUTPUT_TYPE) -> SymbolGrade:
        """Returns whether the symbol passed all Breakout1Model checks."""
        return SymbolGrade(symbol, self.model_type, SymbolGradeValue.PASS) if output.get_val('status') == 'VIABLE' \
            else SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)

    """
    Private methods...
    """

    def _create_time_interval(self,
                              output: Breakout1ModelOutput,
                              interval_start: datetime) -> bool:
        if not self.time().is_open(interval_start):
            output.add_step(passed=False,
                            value=f'market hasn\'t been open long enough to create a '
                            f'{breakout1_constants.BREAKOUT_SETUP_MINS}-minute time period',
                            step_id=Breakout1ModelSteps.INITIALIZATION)
            return False
        output.period = ContinuousTimeInterval(start_time=interval_start.time(), end_time=self.time().now().time())
        return True

    def _load_period_data(self,
                          output: Breakout1ModelOutput,
                          symbol: str) -> bool:
        output.symbol = symbol
        output.period_data = self.get_latest_candles(symbol=symbol, minutes=breakout1_constants.BREAKOUT_SETUP_MINS)
        if not SymbolDay.validate_candles(output.period_data, min_minutes=breakout1_constants.BREAKOUT_SETUP_MINS):
            output.add_step(passed=False,
                            value='insufficient data for the period',
                            step_id=Breakout1ModelSteps.INITIALIZATION)
            return False
        return True

    def _construct_res_line(self,
                            output: Breakout1ModelOutput) -> bool:
        # Construct the resistance line
        output.res_line = TrendLineFinder.find_resistance_line(candles_in_period(
            period=output.period.sub_interval(0, 0.6),
            all_candles=output.period_data,
            day_date=self.time().now().date()))

        # Validate the resistance line
        if output.res_line is None:
            return False

        # Extend and save the resistance line
        output.res_line.extend(output.period_data)
        output.set_val('res_line', output.res_line.to_json())
        return True

    def _construct_sup_line(self,
                            output: Breakout1ModelOutput) -> bool:
        # Construct the support line
        output.sup_line = TrendLineFinder.find_support_line(candles_in_period(
            period=output.period.sub_interval(0, 0.6),
            all_candles=output.period_data,
            day_date=self.time().now().date()))

        # Validate the support line
        if output.sup_line is None:
            return False

        # Extend and save the support line
        output.sup_line.extend(output.period_data)
        output.set_val('sup_line', output.sup_line.to_json())
        return True

    def _dips_to_support(self,
                         output: Breakout1ModelOutput) -> bool:
        dip_interval = output.period.sub_interval(0.45, 0.9)
        dip_candle = min_candle_in_period(period=dip_interval,
                                          candles=output.period_data,
                                          day_date=self.time().now().date())
        if dip_candle is None:
            output.add_step(passed=False,
                            value=f'missing lowest price between '
                            f'{dip_interval.start_time:%H:%M} and '
                            f'{dip_interval.end_time:%H:%M}',
                            step_id=Breakout1ModelSteps.DIPS_TO_SUPPORT)
            return False
        dist_to_sup = dip_candle.low - output.sup_line.y_x(dip_candle.moment)
        output.steps.append(output.check_dist_to_sup(dist_to_sup))
        return output.steps[-1].passed

    def _breaks_resistance(self,
                           output: Breakout1ModelOutput) -> bool:
        break_interval = output.period.sub_interval(0.9, 1)
        break_candle = max_candle_in_period(period=break_interval,
                                            candles=output.period_data,
                                            day_date=self.time().now().date())
        if break_candle is None:
            output.add_step(passed=False,
                            value=f'missing lowest price between '
                            f'{break_interval.start_time:%H:%M} and '
                            f'{break_interval.end_time:%H:%M}',
                            step_id=Breakout1ModelSteps.DIPS_TO_SUPPORT)
            return False
        dist_from_res = break_candle.high - output.res_line.y_x(break_candle.moment)
        output.steps.append(output.check_dist_from_res(dist_from_res))
        return output.steps[-1].passed

    def _check_range_change_1(self,
                              output: Breakout1ModelOutput) -> bool:
        # Calculate the range of the subperiod [0, 0.3]
        subperiod = output.period.sub_interval(0, 0.3)
        subperiod_max = max_candle_in_period(period=subperiod,
                                             candles=output.period_data,
                                             day_date=self.time().now().date())
        if subperiod_max is None:
            output.add_step(passed=False,
                            value=f'missing highest price between '
                            f'{subperiod.start_time:%H:%M} and '
                            f'{subperiod.end_time:%H:%M}',
                            step_id=Breakout1ModelSteps.RANGE_CHANGE_1)
            return False
        subperiod_min = min_candle_in_period(period=subperiod,
                                             candles=output.period_data,
                                             day_date=self.time().now().date())
        if subperiod_min is None:
            output.add_step(passed=False,
                            value=f'missing lowest price between '
                            f'{subperiod.start_time:%H:%M} and '
                            f'{subperiod.end_time:%H:%M}',
                            step_id=Breakout1ModelSteps.RANGE_CHANGE_1)
            return False
        output.range_0 = ((subperiod_max.high + subperiod_max.open) / 2.0) - \
                         ((subperiod_min.low + subperiod_min.open) / 2) \
            if subperiod_max is not None and subperiod_min is not None else 0

        # Calculate the range of the subperiod [0.31, 0.65]
        subperiod = output.period.sub_interval(0.31, 0.65)
        subperiod_max = max_candle_in_period(period=subperiod,
                                             candles=output.period_data,
                                             day_date=self.time().now().date())
        if subperiod_max is None:
            output.add_step(passed=False,
                            value=f'missing highest price between '
                            f'{subperiod.start_time:%H:%M} and '
                            f'{subperiod.end_time:%H:%M}',
                            step_id=Breakout1ModelSteps.RANGE_CHANGE_1)
            return False
        subperiod_min = min_candle_in_period(period=subperiod,
                                             candles=output.period_data,
                                             day_date=self.time().now().date())
        if subperiod_min is None:
            output.add_step(passed=False,
                            value=f'missing lowest price between '
                            f'{subperiod.start_time:%H:%M} and '
                            f'{subperiod.end_time:%H:%M}',
                            step_id=Breakout1ModelSteps.RANGE_CHANGE_1)
            return False
        output.range_1 = ((subperiod_max.high + subperiod_max.open) / 2.0) - \
                         ((subperiod_min.low + subperiod_min.open) / 2)

        # Check that the range decreases from [0, 0.3] to [0.31, 0.65]
        range_change_1 = output.range_1 - output.range_0
        output.steps.append(output.check_range_change_1(range_change_1))
        return output.steps[-1].passed

    def _check_range_change_2(self,
                              output: Breakout1ModelOutput) -> bool:
        # Calculate the range of the subperiod [0.66, 0.85]
        subperiod = output.period.sub_interval(0.66, 0.85)
        subperiod_max = max_candle_in_period(period=subperiod,
                                             candles=output.period_data,
                                             day_date=self.time().now().date())
        if subperiod_max is None:
            output.add_step(passed=False,
                            value=f'missing highest price between '
                            f'{subperiod.start_time:%H:%M} and '
                            f'{subperiod.end_time:%H:%M}',
                            step_id=Breakout1ModelSteps.RANGE_CHANGE_2)
            return False
        subperiod_min = min_candle_in_period(period=subperiod,
                                             candles=output.period_data,
                                             day_date=self.time().now().date())
        if subperiod_min is None:
            output.add_step(passed=False,
                            value=f'missing lowest price between '
                            f'{subperiod.start_time:%H:%M} and '
                            f'{subperiod.end_time:%H:%M}',
                            step_id=Breakout1ModelSteps.RANGE_CHANGE_2)
            return False
        output.range_2 = ((subperiod_max.high + subperiod_max.open) / 2.0) - \
                         ((subperiod_min.low + subperiod_min.open) / 2)

        # Check that the range decreases from [0.31, 0.65] to [0.65, 0.85]
        range_change_2 = output.range_2 - output.range_1
        output.steps.append(output.check_range_change_2(range_change_2))
        return output.steps[-1].passed

    def _check_max_reward(self,
                          output: Breakout1ModelOutput) -> bool:
        midpoint_candle = midpoint_candle_in_period(period=output.period,
                                                    candles=output.period_data,
                                                    day_date=self.time().now().date())
        if midpoint_candle is None:
            output.add_step(passed=False,
                            value='missing midpoint candle in the period',
                            step_id=Breakout1ModelSteps.MAX_REWARD)
            return False
        output.set_val('midpoint_x', midpoint_candle.moment)
        output.set_val('midpoint_sup_y', output.sup_line.y_x(midpoint_candle.moment))
        output.set_val('midpoint_res_y', output.res_line.y_x(midpoint_candle.moment))
        max_reward = output.res_line.y_x(midpoint_candle.moment) - output.sup_line.y_x(midpoint_candle.moment)
        output.add_step(step=output.check_max_reward(max_reward))
        return output.steps[-1].passed

    def _check_high_volume_drop_ratio(self,
                                      output: Breakout1ModelOutput) -> bool:
        # Calculate minute-to-minute statistics (mean and stdev of |high - low| and volume)
        output.minute_candles = aggregate_minute_candles(output.period_data)
        output.minute_ranges = [candle.high - candle.low for candle in output.minute_candles]
        output.minute_volumes = [candle.volume for candle in output.minute_candles]
        output.avg_minute_range = mean([abs(price_range) for price_range in output.minute_ranges])
        output.stdev_minute_range = stdev([abs(price_range) for price_range in output.minute_ranges])
        output.avg_minute_volume = mean(output.minute_volumes)
        output.stdev_minute_volume = stdev(output.minute_volumes)

        # Check that the price doesn't drop too often when the minute's volume increases
        output.high_volume_mins = [candle for candle in output.minute_candles
                                   if candle.volume > output.avg_minute_volume + 1.5 * output.stdev_minute_volume]
        high_volume_drop_ratio = len(
            [min_range for min_range in output.minute_ranges
             if min_range < -output.avg_minute_range - 0.5 * output.stdev_minute_range
             ]) / len(output.high_volume_mins)
        output.steps.append(output.check_high_volume_drop_ratio(high_volume_drop_ratio))
        return output.steps[-1].passed

    def _check_strongest_high_volume_dip(self,
                                         output: Breakout1ModelOutput) -> bool:
        # Check that the strongest high-volume dip is not more than 1.7 standard deviations stronger
        # than the average minute's |high-low|
        strongest_high_volume_dip = \
            max([candle.high - candle.low for candle in output.high_volume_mins
                 if candle.volume > output.avg_minute_volume + 1.5 * output.stdev_minute_volume
                 and candle.open > candle.close])
        output.steps.append(output.check_strongest_high_volume_dip(strongest_high_volume_dip))
        return output.steps[-1].passed

    def _check_ema_volume_excitement(self,
                                     output: Breakout1ModelOutput) -> bool:
        ema_volumes = [ema(output.minute_volumes)]
        prev_date = self.time().now().date()
        for i in range(7):
            # Load the previous day's data
            prev_date = self.time().get_prev_mkt_day(prev_date)
            day_data = self.mongo().load_symbol_day(output.symbol, prev_date)
            if not SymbolDay.validate_candles(day_data.candles):
                output.steps.append(ModelStep(passed=False,
                                              value=f'missing needed data on {prev_date.strftime(DATE_FORMAT)}',
                                              step_id=Breakout1ModelSteps.EMA_MINUTE_VOLUME))
                return False

            # Aggregate the day's second-resolution candles into minute resolution
            prev_period_start = datetime.combine(prev_date, output.period.start_time)
            prev_period_end = datetime.combine(prev_date, output.period.end_time)
            prev_second_candles = [candle for candle in day_data.candles
                                   if prev_period_start <= candle.moment <= prev_period_end]
            prev_minute_candles = aggregate_minute_candles(prev_second_candles)

            # Calculate the previous day's moving-average volume
            ema_volumes.append(ema([candle.volume for candle in prev_minute_candles]))

        # Calculate the median ema volume of the same period on each of the past 7 days
        med_ema_volume_prev_7_periods = median(ema_volumes)
        # Calculate the ema volume of this period today
        ema_minute_volume = ema(output.minute_volumes)
        # Perform next step: ema minute volume check
        output.steps.append(output.check_ema_minute_volume(ema_minute_volume, med_ema_volume_prev_7_periods))
        return output.steps[-1].passed
