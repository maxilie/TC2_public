from datetime import datetime
from statistics import mean
from typing import List

from tc2.data.data_structs.price_data.Candle import Candle


class SimpleLinearRegression:
    """
    Contains a simple linear regression line, y = B_0 + B_1 * x.
    """

    # The candles used to generate this regression line
    candles: List[Candle]

    # The slope of the line (price per second)
    slope: float

    # The y-intercept of the line (price at origin moment)
    y_int: float

    # The moment in time at the y-intercept
    origin_moment: datetime

    def __init__(self,
                 candles: List[Candle]):
        # Set price data
        self.candles = candles

        # Set origin moment to the first moment in the data
        self.origin_moment = candles[0].moment

        # Get x and y points
        x_vals = [self.moment_to_x(candle.moment) for candle in candles]
        y_vals = [candle.open for candle in candles]

        # Calculate x_bar and y_bar
        x_bar = mean(x_vals)
        y_bar = mean(y_vals)

        # Calculate s_xx and s_xy
        s_xx = sum(pow(x - x_bar, 2) for x in x_vals)
        s_xy = sum((x_vals[i] - x_bar) * (y_vals[i] - y_bar) for i in range(len(x_vals)))

        # Calculate slope and y-intercept
        self.slope = s_xy / s_xx
        self.y_int = y_bar - self.slope * x_bar

    def y_of_x(self,
               x_moment: datetime) -> float:
        """
        Evaluates the regression line function at the given moment, returning a price value.
        """
        return self.y_int + self.moment_to_x(x_moment) * self.slope

    def moment_to_x(self,
                    x_moment: datetime) -> float:
        """
        Converts a moment in time to a decimal number relative to the line's starting time.
        """
        return (x_moment - self.origin_moment).total_seconds()
