import traceback
from datetime import datetime, timedelta
from typing import List

from tc2.data.data_structs.price_data.Candle import Candle
from tc2.stock_analysis.analysis_structs.SimpleLinearRegression import SimpleLinearRegression
from tc2.util.candle_util import find_mins_maxs
from tc2.util.data_constants import START_DATE
from tc2.util.market_util import OPEN_TIME


class BoundedLinearRegressions:
    """
    Performs two linear regressions over a trendline period:
        + one line fitted through the local minima of prices
        + one line fitted through the local maxima of prices
    """

    candles: List[Candle]
    local_minima: List[Candle]
    local_maxima: List[Candle]
    minima_regression: SimpleLinearRegression
    maxima_regression: SimpleLinearRegression

    def __init__(self,
                 trendline_candles: List[Candle]):
        """
        Fits regression lines through local minima and maxima of prices during the trendline period.
        """
        self.candles = trendline_candles
        try:
            self.local_minima, self.local_maxima = find_mins_maxs(trendline_candles)
            self.minima_regression = SimpleLinearRegression(self.local_minima)
            self.maxima_regression = SimpleLinearRegression(self.local_maxima)
        except Exception as e:
            traceback.print_exc()
            try:
                moment_1 = datetime.combine(START_DATE, OPEN_TIME) + timedelta(seconds=1)
                moment_2 = datetime.combine(START_DATE, OPEN_TIME) + timedelta(seconds=2)
                candle_1 = Candle(moment_1, 0, 0, 0, 0, 1)
                candle_2 = Candle(moment_2, 0, 0, 0, 0, 1)
                self.candles = [candle_1, candle_2]
                self.local_minima = [candle_1, candle_2]
                self.local_maxima = [candle_1, candle_2]
                self.minima_regression = SimpleLinearRegression([candle_1, candle_2])
                self.maxima_regression = SimpleLinearRegression([candle_1, candle_2])
            except Exception as e:
                traceback.print_exc()
