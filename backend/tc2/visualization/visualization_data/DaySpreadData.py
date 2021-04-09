import json
import statistics
from datetime import datetime, timedelta
from typing import Dict

from tc2.env.ExecEnv import ExecEnv
from tc2.util.market_util import OPEN_TIME
from tc2.visualization.VisualType import VisualType
from tc2.visualization.visualization_data.AbstractVisualizationData import AbstractVisualizationData


class DaySpreadData(AbstractVisualizationData):
    """Contains the variables required to create a day spread chart."""

    symbol: str
    med_spread_str: str
    volatile_str: str
    data: str

    def __init__(self, symbol: str, med_spread_str: str, volatile_str: str, data: str) -> None:
        super().__init__(VisualType.DAY_SPREAD)
        self.symbol = symbol
        self.med_spread_str = med_spread_str
        self.volatile_str = volatile_str
        self.data = data

    def get_id(self) -> str:
        return self.visual_type.value + '_' + self.symbol

    def to_json(self) -> Dict:
        return {'med_day_spread': self.med_spread_str,
                'volatile_str': self.volatile_str,
                'data': self.data}

    @classmethod
    def generate_data(cls, live_env: ExecEnv,
                      sim_env: ExecEnv,
                      **kwargs) -> 'AbstractVisualizationData':
        """
        Compiles the symbol's price data into a json string usable by the visualization script.
        :keyword: symbol: str
        """

        # Extract parameters
        symbol: str = kwargs['symbol']

        # Format price data so it can be made into a graph
        day_date = (datetime.today() - timedelta(days=1)).date()
        pct_spreads = []
        while len(pct_spreads) < 31:
            day_date = day_date - timedelta(days=1)

            # Skip days on which markets are closed
            if not live_env.time().is_open(datetime.combine(day_date, OPEN_TIME)):
                continue

            # Load data for the day
            day_data = live_env.mongo().load_symbol_day(symbol, day_date)

            # Calculate the day's price spread (difference between highest and lowest price)
            highest_price = max([candle.open for candle in day_data.candles])
            lowest_price = min([candle.open for candle in day_data.candles])
            pct_spreads.append(100 * (highest_price - lowest_price) / lowest_price)

        # Calculate median pct_spread
        median_spread = 0 if len(pct_spreads) == 0 else statistics.median(pct_spreads)

        # Sum up frequencies of spreads in each bin
        bins_dict = {'<0.4%': 0,
                     '0.4% - 0.8%': 0,
                     '0.8% - 1.2%': 0,
                     '1.2% - 1.6%': 0,
                     '1.6% - 2.1%': 0,
                     '>2.1%': 0}
        for spread in pct_spreads:
            if spread < 0.4:
                bins_dict['<0.4%'] += 1
            elif spread < 0.8:
                bins_dict['0.4% - 0.8%'] += 1
            elif spread < 1.2:
                bins_dict['0.8% - 1.2%'] += 1
            elif spread < 1.6:
                bins_dict['1.2% - 1.6%'] += 1
            elif spread < 2.1:
                bins_dict['1.6% - 2.1%'] += 1
            else:
                bins_dict['>2.1%'] += 1

        # Add json object to data array for each bin
        data = []
        for bin_name, frequency in bins_dict.items():
            data.append({'name': bin_name,
                         'frequency': str(frequency)})

        # Say whether the symbol is volatile enough to percentage and string
        volatility_str = 'volatile' if median_spread >= 0.008 else 'not volatile'

        # Return the price graph data in a neat object
        return DaySpreadData(symbol, f'{median_spread:.1f}', volatility_str, json.dumps(data))
