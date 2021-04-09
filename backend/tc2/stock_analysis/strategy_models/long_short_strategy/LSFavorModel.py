from datetime import timedelta, datetime
from typing import List

from tc2.data.data_structs.price_data.Candle import Candle
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.stock_analysis.AbstractSpotModel import AbstractSpotModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade, SymbolGradeValue
from tc2.stock_analysis.analysis_structs.BoundedLinearRegression import BoundedLinearRegressions
from tc2.stock_analysis.strategy_models.long_short_strategy.LongShortFavor import LongShortFavor
from tc2.util.TimeInterval import ContinuousTimeInterval
from tc2.util.candle_util import candles_in_period


class LSFavorModel(AbstractSpotModel):
    """
    Uses a historically-validated way to measure which direction the S&P-500 is
        trending in, during the short-term.

    LongShortStrategy can use the direction and magnitude of the market's trend to place
        a higher bet in the direction of the trend.
    """

    # Output indicates whether we should buy more shares in SPXL or SPXS.
    OUTPUT_TYPE = LongShortFavor

    def calculate_output(self,
                         symbol: str) -> OUTPUT_TYPE:
        """
        Returns a number between -1 and 1, indicating how strongly the S&P-500 is trending
            and in which direction.
        """

        # Do not allow symbols to execute LongShortStrategy except SPXS and SPXL.
        if symbol not in ['SPXL', 'SPXS']:
            return LongShortFavor.NOT_APPLICABLE

        # Fetch data during the period.
        spxl_candles = self.get_latest_candles('SPXL', 30)
        spxs_candles = self.get_latest_candles('SPXS', 30)

        # Validate data.
        debugger = []
        for candles in [spxl_candles, spxs_candles]:
            if not SymbolDay.validate_candles(candles,
                                              min_minutes=int(29),
                                              debug_output=debugger):
                debug_str = '\n\t'.join(debugger)
                self.debug_process(f'LSFavor invalid data')
                raise ValueError('LSFavorModel could not fetch valid data')

        # self.debug_process(f'LSFavor using candles to get favor val')
        return self.get_favor_val(self.time().now(), spxl_candles, spxs_candles)

    def get_favor_val(self,
                      moment: datetime,
                      spxl_candles_30: List[Candle],
                      spxs_candles_30: List[Candle]) -> LongShortFavor:
        """
        Returns a prediction of which direction (long or short) is more likely to
        generate more immediate profit, based on the Bounded Linear Regressions trendline.
        :param spxl_candles_30: the past 30 minutes of SPXL's price data
        :param spxs_candles_30: the past 30 minutes of SPXS's price data
        """

        # Calculate BLR's for 3, 10, and 25 minute periods.
        blr_3_period = ContinuousTimeInterval((moment - timedelta(seconds=3 * 60)).time(),
                                              moment.time())
        blr_10_period = ContinuousTimeInterval((moment - timedelta(seconds=10 * 60)).time(),
                                               moment.time())
        blr_25_period = ContinuousTimeInterval((moment - timedelta(seconds=25 * 60)).time(),
                                               moment.time())

        # Calculate BLR trendline indicators.
        spxl_blr_3 = self.get_blr_strength(BoundedLinearRegressions(
            candles_in_period(blr_3_period, spxl_candles_30, moment.date())))
        spxs_blr_3 = self.get_blr_strength(BoundedLinearRegressions(
            candles_in_period(blr_3_period, spxs_candles_30, moment.date())))
        spxl_blr_10 = self.get_blr_strength(BoundedLinearRegressions(
            candles_in_period(blr_10_period, spxl_candles_30, moment.date())))
        spxs_blr_10 = self.get_blr_strength(BoundedLinearRegressions(
            candles_in_period(blr_10_period, spxs_candles_30, moment.date())))
        spxl_blr_25 = self.get_blr_strength(BoundedLinearRegressions(
            candles_in_period(blr_25_period, spxl_candles_30, moment.date())))
        spxs_blr_25 = self.get_blr_strength(BoundedLinearRegressions(
            candles_in_period(blr_25_period, spxs_candles_30, moment.date())))

        # Ensure spxl and spxs trends are not simultaneously positive.
        if (spxl_blr_3 > 0.6 and spxs_blr_3 > 0.6) or \
                (spxl_blr_10 > 0.6 and spxs_blr_10 > 0.6) or \
                (spxl_blr_25 > 0.6 and spxs_blr_25 > 0.6):
            raise ValueError(f'LSFavorModel couldn\'t make a prediction because trend strength '
                             f'is somehow positive in both directions')

        if spxl_blr_3 > 0.65 and spxl_blr_10 > 0.65 and spxl_blr_25 < 0.5:
            return LongShortFavor.SPXL_STRONGLY_FAVORED
        elif (spxl_blr_3 > 0.65 or spxl_blr_10 > 0.65) and spxl_blr_25 < 0.5:
            return LongShortFavor.SPXL_FAVORED

        if spxs_blr_3 > 0.65 and spxs_blr_10 > 0.65 and spxs_blr_25 < 0.5:
            return LongShortFavor.SPXS_STRONGLY_FAVORED
        elif (spxs_blr_3 > 0.65 or spxs_blr_10 > 0.65) and spxs_blr_25 < 0.5:
            return LongShortFavor.SPXS_FAVORED

        return LongShortFavor.NO_FAVOR

    def get_blr_strength(self,
                         blr: BoundedLinearRegressions) -> float:
        """
        Returns the signal strength of a Bounded Linear Regressions trendline (-1 to 1).
        """
        # Return 0 if slopes are different signs.
        if blr.minima_regression.slope * blr.maxima_regression.slope < 0:
            return 0

        # Return 0 if not enough data.
        if len(blr.candles) <= 3:
            return 0

        # Find high and low prices of the trendline period.
        high_price = max([candle.high for candle in blr.candles])
        low_price = max([candle.low for candle in blr.candles])

        # Find start and end of the period.
        start_moment = max([candle.moment for candle in blr.candles])
        end_moment = min([candle.moment for candle in blr.candles])

        # Take signal strength to be the average of the two slopes.
        minima_slope_pct = abs(blr.minima_regression.y_of_x(end_moment) - blr.minima_regression.y_of_x(start_moment)) \
                           / max(0.01, high_price - low_price)
        maxima_slope_pct = abs(blr.maxima_regression.y_of_x(end_moment) - blr.maxima_regression.y_of_x(start_moment)) \
                           / max(0.01, high_price - low_price)
        signal_strength = (minima_slope_pct + maxima_slope_pct) / 2.0

        # Scale down signal strength.
        signal_strength = min(1, signal_strength / 5.0)

        # Ensure the signal strength has the correct sign.
        if blr.minima_regression.slope < 0:
            signal_strength += -1

        return signal_strength

    def grade_symbol(self,
                     symbol: str,
                     output: OUTPUT_TYPE) -> SymbolGrade:
        """
        Always assigns a passing grade.
        """
        # Assign a passing grade if the symbol is to be ignored.
        if output is LongShortFavor.NOT_APPLICABLE:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.PASS)

        # TEMPORARY: Always assign a passing grade.
        return SymbolGrade(symbol, self.model_type, SymbolGradeValue.PASS)
