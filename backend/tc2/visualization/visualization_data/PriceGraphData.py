import json
from datetime import datetime, timedelta
from typing import Dict

from tc2.env.ExecEnv import ExecEnv
from tc2.util.data_constants import START_DATE, MIN_CANDLES_PER_MIN
from tc2.util.date_util import DATE_TIME_FORMAT
from tc2.util.market_util import OPEN_TIME
from tc2.visualization.VisualType import VisualType
from tc2.visualization.visualization_data.AbstractVisualizationData import AbstractVisualizationData


class PriceGraphData(AbstractVisualizationData):
    """Contains the variables required to create a price graph page using the html template."""

    symbol: str
    valid_days: int
    total_days: int
    data: str
    last_updated: datetime

    def __init__(self, symbol: str, valid_days: int, total_days: int, data: str, last_updated: datetime) -> None:
        super().__init__(VisualType.PRICE_GRAPH)
        self.symbol = symbol
        self.valid_days = valid_days
        self.total_days = total_days
        self.data = data
        self.last_updated = last_updated

    def get_id(self) -> str:
        return self.visual_type.value + '_' + self.symbol

    def to_json(self) -> Dict:
        return {'price_graph_data': self.data,
                'valid_days': self.valid_days,
                'total_days': self.total_days,
                'last_updated': self.last_updated.strftime(DATE_TIME_FORMAT)}

    @classmethod
    def generate_data(cls, live_env: ExecEnv,
                      sim_env: ExecEnv,
                      **kwargs) -> 'PriceGraphData':
        """
        Compiles the symbol's price data into a json string usable by the graphing script.
        :keyword: symbol
        """

        # Extract parameters
        symbol: str = kwargs['symbol']

        # Format price data so it can be made into a graph
        json_array = []
        day_date = START_DATE
        end_date = (datetime.today() - timedelta(days=1)).date()
        valid_days = 0
        invalid_days = 0
        while day_date <= end_date:
            day_date = day_date + timedelta(days=1)

            # Skip days on which markets are closed
            if not live_env.time().is_open(datetime.combine(day_date, OPEN_TIME)):
                continue

            # Denote missing data with price=0, valid_minutes=0
            day_data = live_env.mongo().load_symbol_day(symbol, day_date)
            if day_data is None or len(day_data.candles) == 0:
                invalid_days += 1
                json_array.append({"date": "{}/{}/{}".format(day_date.month, day_date.day, day_date.year),
                                   "price": "0",
                                   "valid_minutes": "0"})
                continue

            valid_days += 1

            # Find the open price and the number of minutes with at least 5 candles
            open_price = day_data.candles[0].open
            valid_mins = 0
            candles_in_min = 0
            last_min = day_data.candles[0].moment.replace(second=0) - timedelta(minutes=1)
            for candle in day_data.candles:
                if candle.moment.replace(second=0) >= last_min + timedelta(seconds=1):
                    if candles_in_min >= MIN_CANDLES_PER_MIN:
                        valid_mins += 1
                    last_min = candle.moment.replace(second=0)
                    candles_in_min = 0
                else:
                    candles_in_min += 1

            # Create a json object (data point) corresponding to the day
            json_array.append({"date": "{}/{}/{}".format(day_date.month, day_date.day, day_date.year),
                               "price": str(open_price),
                               "valid_minutes": str(valid_mins)})

        # Return the price graph data in a neat object
        return PriceGraphData(symbol=symbol,
                              valid_days=valid_days,
                              total_days=valid_days + invalid_days,
                              data=json.dumps(json_array),
                              last_updated=live_env.time().now())
