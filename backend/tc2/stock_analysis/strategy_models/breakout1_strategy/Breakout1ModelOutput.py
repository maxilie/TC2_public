from datetime import date, datetime
from typing import List

from tc2.stock_analysis.ModelWeightingSystem import SymbolGradeValue
from tc2.stock_analysis.strategy_models.breakout1_strategy.Breakout1ModelSteps import Breakout1ModelSteps
from tc2.stock_analysis.model_output.AbstractModelOutput import AbstractModelOutput
from tc2.stock_analysis.model_output.ModelStep import ModelStep
from tc2.stock_analysis.model_output.PriceLine import PriceLine
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.util.TimeInterval import ContinuousTimeInterval
from tc2.util.date_util import DATE_FORMAT


class Breakout1ModelOutput(AbstractModelOutput):
    """Contains variables used to check whether a symbol is viable for Breakout1Strategy."""

    # The date on which the stock was evaluated
    day_date: date

    # A pass/fail grade indicating whether the symbol is viable
    viability_status: SymbolGradeValue

    # A continuous time interval during the current market day
    time_period: ContinuousTimeInterval

    # The period's lowest price
    period_low: float = None

    # The period's high minus its low
    period_range: float = None

    # The period's resistance line
    res_line: PriceLine = None

    # The period's support line
    sup_line: PriceLine = None

    # Variables for drawing the setup's max reward
    midpoint_x: datetime
    midpoint_sup_y: float
    midpoint_res_y: float

    # Mean and standard deviation of the minute-to-minute |high - low| and volume
    avg_minute_range: float = None
    stdev_minute_range: float = None
    avg_minute_volume: float = None
    stdev_minute_volume: float = None

    # Temp variables that don't get returned in JSON
    symbol: str
    period: ContinuousTimeInterval
    period_data: List[Candle]
    minute_volumes: List[int]
    range_0: float
    range_1: float
    range_2: float
    high_volume_mins: List[Candle]

    def __init__(self, day_date: date):
        super().__init__()
        self.day_date = day_date
        self.set_val('day_date', day_date.strftime(DATE_FORMAT))
        self.set_val('status', 'NOT_VIABLE')

    def check_dist_to_sup(self,
                          dist_to_sup: float) -> ModelStep:
        """
        Returns whether the price dipped to slightly above or just barely below the support.
        :param dist_to_sup: difference between the symbol's recent low and the support line
        """
        return ModelStep(passed=self.period_range * -15 / 100 <= dist_to_sup <= self.period_range * 20 / 100,
                         value=f'{100 * dist_to_sup / self.period_range:.2f}%',
                         step_id=Breakout1ModelSteps.DIPS_TO_SUPPORT)

    def check_dist_from_res(self,
                            dist_from_res: float) -> ModelStep:
        """
        Returns whether the price exceeded the resistance line by at least 10% of the period's range.
        :param dist_from_res: difference between the resistance line and the symbol's recent high
        """
        return ModelStep(passed=dist_from_res >= 0.1 * self.period_range,
                         value=f'{100 * dist_from_res / self.period_range:.2f}%',
                         step_id=Breakout1ModelSteps.BREAKS_RESISTANCE)

    def check_range_change_1(self,
                             range_change_1: float) -> ModelStep:
        """
        Returns whether the range decreased from [0, 0.3t] to [0.31t, 0.65t].
        :param range_change_1: change in price range between [0, 0.3t] and [0.31t, 0.65t]
        """
        return ModelStep(passed=range_change_1 / self.period_low < 0.1,
                         value=f'{100 * range_change_1 / self.period_low:0.2f}%',
                         step_id=Breakout1ModelSteps.RANGE_CHANGE_1)

    def check_range_change_2(self,
                             range_change_2: float) -> ModelStep:
        """
        Returns whether the range decreased from [0.31t, 0.65t] to [0.66t, 0.85t].
        :param range_change_2: change in price range between [0.66, 0.85t] and [0.66t, 0.85t]
        """
        return ModelStep(passed=range_change_2 / self.period_low < 0.1,
                         value=f'{100 * range_change_2 / self.period_low:0.2f}%',
                         step_id=Breakout1ModelSteps.RANGE_CHANGE_2)

    def check_max_reward(self,
                         max_reward: float) -> ModelStep:
        """
        Returns whether the profit upper bound is acceptably high.
        :param max_reward: highest profit to sell for: res_line - sup_line at 0.5t
        """
        return ModelStep(passed=max_reward / self.period_low > 0.15 / 100,
                         value=f'{100 * max_reward / self.period_low:.2f}%',
                         step_id=Breakout1ModelSteps.MAX_REWARD)

    def check_high_volume_drop_ratio(self,
                                     high_volume_drop_ratio: float) -> ModelStep:
        """
        Returns whether the price drops too often when volume increases.
        :param high_volume_drop_ratio: when a minute's volume is higher than usual, the pct of occurrences
            that see price drop
        """
        self.set_val('high_volume_drop_ratio', high_volume_drop_ratio)
        return ModelStep(passed=high_volume_drop_ratio > 1.5,
                         value=f'{high_volume_drop_ratio}:1',
                         step_id=Breakout1ModelSteps.HIGH_VOL_DROP_RATIO)

    def check_strongest_high_volume_dip(self,
                                        strongest_high_volume_dip: float) -> ModelStep:
        """
        Returns whether any single minute with atypically high volume drops in price too steeply.
        :param strongest_high_volume_dip: strongest minute-resolution price drop that is accompanied by
            higher-than-usual volume
        """

        return ModelStep(passed=strongest_high_volume_dip < self.avg_minute_range + (1.7 * self.stdev_minute_range),
                         value=f'{(strongest_high_volume_dip - self.avg_minute_range) / self.stdev_minute_range:.0f} '
                         f'stdevs',
                         step_id=Breakout1ModelSteps.STRONGEST_HIGH_VOL_DIP)

    def check_ema_minute_volume(self,
                                ema_minute_volume: float,
                                med_ema_volume_prev_7_periods: float) -> ModelStep:
        """
        Returns whether this period's moving-average volume is higher than the median of the moving-average volume
        during the same period on the previous 7 days.
        :param ema_minute_volume: average minute's volume exponentially weighted by time
        :param med_ema_volume_prev_7_periods: median of: moving-average volume during the same period on each of
            the last 7 days
        """

        return ModelStep(passed=ema_minute_volume > 1.2 * med_ema_volume_prev_7_periods,
                         value=f'{100 * ema_minute_volume / med_ema_volume_prev_7_periods:.1f}%',
                         step_id=Breakout1ModelSteps.EMA_MINUTE_VOLUME)
