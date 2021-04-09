from datetime import datetime, date
from typing import Dict, List

from tc2.env.ExecEnv import ExecEnv
from tc2.strategy.strategies.swing1.SwingStrategy import SwingStrategy
from tc2.util.data_constants import START_DATE
from tc2.util.date_util import DATE_TIME_FORMAT, DATE_FORMAT
from tc2.visualization.VisualType import VisualType
from tc2.visualization.visualization_data.AbstractVisualizationData import AbstractVisualizationData


class SwingViableDay:
    """Contains json-serializable info on a single day that was viable for SwingStrategy."""

    # The date on which the symbol was viable for SwingStrategy
    day_date: date
    # The volume of the day before day_date
    prev_day_volume: int
    # The average volume of the 50 days preceding the day before day_date
    avg_volume_50: int
    # The price range for the 75 days preceding the day before day_date
    range_75: float
    # The highest price attained on the day before day_date
    prev_day_high: float

    def __init__(self, day_date: date,
                 prev_day_volume: int,
                 avg_volume_50: int,
                 range_75: float,
                 prev_day_high: float):
        self.day_date = day_date
        self.prev_day_volume = prev_day_volume
        self.avg_volume_50 = avg_volume_50
        self.range_75 = range_75
        self.prev_day_high = prev_day_high

    def to_json(self) -> Dict[str, any]:
        """Converts the data into a json-serializable dictionary so it can be used in a visual webpage display."""
        return {
            'day_date': self.day_date.strftime(DATE_FORMAT),
            'prev_day_volume': self.prev_day_volume,
            'avg_volume_50': self.avg_volume_50,
            'range_75': self.range_75,
            'prev_day_high': self.prev_day_high
        }


class SwingSetupData(AbstractVisualizationData):
    """
    Contains the variables required to draw a price graph with a marker at each day that's viable to SwingStrategy.
    """

    # The symbol for which to generate the visual
    symbol: str
    # Ex. [{'day_date': '2020/1/2', 'open': xx.xx, 'high': xx.xx, 'low': xx.xx, 'close': xx.xx}, ...]
    daily_candles: List[Dict]
    # SwingStrategy-viable days with details into why each day was viable
    #   Ex. [{'day_date': '2020/1/2', 'prev_day_volume': xxx, ...}, ...]
    viable_days: List[Dict]
    # Moment the visual was last updated for the symbol
    last_updated: datetime

    def __init__(self, symbol: str,
                 daily_candles: List[Dict],
                 viable_days: List[Dict],
                 last_updated: datetime) -> None:
        super().__init__(VisualType.SWING_SETUP)
        self.symbol = symbol
        self.daily_candles = daily_candles
        self.viable_days = viable_days
        self.last_updated = last_updated

    def get_id(self) -> str:
        return self.visual_type.value + '_' + self.symbol

    def to_json(self) -> Dict[str, any]:
        return {
            'daily_candles': self.daily_candles,
            'viable_days': self.viable_days,
            'last_updated': self.last_updated.strftime(DATE_TIME_FORMAT)
        }

    @classmethod
    def generate_data(cls, live_env: ExecEnv,
                      sim_env: ExecEnv,
                      **kwargs) -> 'SwingSetupData':
        """
        Compiles the symbol's price data into a json string usable by the graphing script.
        :keyword: symbol
        """

        # Extract parameters
        symbol: str = kwargs['symbol']

        # Get a list of dates with data on file
        dates_on_file = live_env.mongo().get_dates_on_file(symbol, START_DATE, live_env.time().now())
        if len(dates_on_file) < 30:
            live_env.warn_process(f'Couldn\'t generate SwingSetupData for {symbol} because it only has '
                                  f'{len(dates_on_file)} days of price data stored in mongo')
            return SwingSetupData._blank_swing_setup_data(symbol, live_env.time().now())

        swing_viable_days: List[SwingViableDay] = []

        # Create a SwingStrategy so we can test viability
        strategy = SwingStrategy(env=sim_env, symbols=[symbol])

        for day_date in dates_on_file:
            # TODO Copy day_date's data from the live environment into the simulation environment

            # TODO Test viability of SwingStrategy on day_date

            # TODO Feed models on day_date
            pass

        # Load all daily aggregate candles for the symbol
        daily_candles = [live_env.mongo().load_aggregate_candle(day_date) for day_date in dates_on_file]

        # Return the price graph data in a neat object
        return SwingSetupData(symbol=symbol,
                              daily_candles=[daily_candle.to_json() for daily_candle in daily_candles if
                                             daily_candle is not None],
                              viable_days=[viable_day.to_json() for viable_day in swing_viable_days],
                              last_updated=live_env.time().now())

    @classmethod
    def _blank_swing_setup_data(cls, symbol: str, moment: datetime) -> 'SwingSetupData':
        """Returns a blank SwingSetupData (used when the data cannot be generated)."""
        return SwingSetupData(symbol=symbol,
                              daily_candles=[],
                              viable_days=[],
                              last_updated=moment)
