from datetime import datetime
from typing import Dict, List

from tc2.data.data_structs.price_data.Candle import Candle
from tc2.util.date_util import DATE_TIME_FORMAT


class PriceLine:
    """Represents a line on a price graph drawn between two points."""

    # The x and y for the first point
    point_1_moment: datetime
    point_1_price: float

    # The x and y for the second point
    point_2_moment: datetime
    point_2_price: float

    # The first and last x values of period for which to draw the line
    first_moment: datetime
    last_moment: datetime

    # The slope of the line (price per second)
    slope: float

    # The y-intercept of the line (assuming (0, f(0)) is (point_1_moment, point_1_price) )
    y_int: float

    def __init__(self, point_1_moment: datetime,
                 point_1_price: float,
                 point_2_moment: datetime,
                 point_2_price: float,
                 first_moment: datetime,
                 last_moment: datetime):
        # Set variables
        self.point_1_moment = point_1_moment
        self.point_1_price = point_1_price
        self.point_2_moment = point_2_moment
        self.point_2_price = point_2_price
        self.first_moment = first_moment
        self.last_moment = last_moment
        self.y_int = point_1_price

        # Calculate slope
        self.slope = (self.point_2_price - self.point_1_price) \
                     / (self.point_2_moment - self.point_1_moment).total_seconds()

    def y_x(self, x: datetime) -> float:
        """Evaluates the line function at the given moment, returning a price prediction."""
        return self.point_1_price + self.slope * ((x - self.point_1_moment).total_seconds())

    def extend(self,
               period_data: List[Candle]) -> None:
        """
        Extends the length of the line without changing its slope.
        """
        self.point_1_moment = period_data[0].moment
        self.point_1_price = period_data[0].open
        self.point_2_moment = period_data[1].moment
        self.point_2_price = period_data[1].open

    def to_json(self) -> Dict[str, any]:
        """Converts the PriceLine into a json dictionary that can be used to overlay a line on a price graph."""
        return {
            'x_0': self.point_1_moment.strftime(DATE_TIME_FORMAT),
            'y_0': self.point_1_price,
            'x_1': self.point_2_moment.strftime(DATE_TIME_FORMAT),
            'y_1': self.point_2_price,
            'x_first': self.first_moment.strftime(DATE_TIME_FORMAT),
            'y_first': self.y_x(self.first_moment),
            'x_last': self.last_moment.strftime(DATE_TIME_FORMAT),
            'y_last': self.y_x(self.last_moment)
        }
