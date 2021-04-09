from datetime import datetime
from typing import Dict, List

from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.stock_analysis.strategy_models.breakout1_strategy.Breakout1Model import Breakout1Model
from tc2.stock_analysis.strategy_models.breakout1_strategy.Breakout1ModelOutput import Breakout1ModelOutput
from tc2.data.stock_data_collection.ModelFeeder import ModelFeeder
from tc2.env.ExecEnv import ExecEnv
from tc2.util import candle_util
from tc2.util.candle_util import aggregate_minute_candles
from tc2.util.date_util import DATE_TIME_FORMAT
from tc2.visualization.VisualType import VisualType
from tc2.visualization.visualization_data.AbstractVisualizationData import AbstractVisualizationData


class Breakout1SetupData(AbstractVisualizationData):
    """
    Contains the variables required to draw a minute-resolution price graph with a Breakout1Strategy
    resistance and support line overlain.
    """

    # The symbol for which to generate the visual
    symbol: str
    # Day + time to check the viability for the symbol
    check_moment: datetime
    # List of the full day's minute-resolution candles
    day_data: List[Dict[str, any]]
    # Json data from the day's Breakout1ModelOutput
    model_data: Dict[str, any]
    # Moment the visual was last updated for the symbol
    last_updated: datetime

    def __init__(self, symbol: str,
                 check_moment: datetime,
                 day_data: List[Dict],
                 model_data: Dict[str, any],
                 last_updated: datetime) -> None:
        super().__init__(VisualType.BREAKOUT1_SETUP)
        self.symbol = symbol
        self.check_moment = check_moment
        self.day_data = day_data
        self.model_data = model_data
        self.last_updated = last_updated

    def get_id(self) -> str:
        return self.visual_type.value + '_' + self.symbol

    def to_json(self) -> Dict[str, any]:
        return {
            'symbol': self.symbol,
            'check_moment': self.check_moment.strftime(DATE_TIME_FORMAT),
            'day_data': self.day_data,
            'model_data': self.model_data,
            'last_updated': self.last_updated.strftime(DATE_TIME_FORMAT)
        }

    @classmethod
    def generate_data(cls, live_env: ExecEnv,
                      sim_env: ExecEnv,
                      **kwargs) -> 'Breakout1SetupData':
        """
        Compiles the symbol's price data into a json string usable by the graphing script.
        :keyword: symbol
        """

        # Extract parameters
        symbol: str = kwargs['symbol']
        check_moment: datetime = kwargs['check_moment']

        live_env.info_process(f'Generating breakout1 setup visual for {symbol} '
                              f'at {check_moment.strftime(DATE_TIME_FORMAT)}')

        # Set simulated environment's time to check_moment
        sim_env.time().set_moment(check_moment)

        # Copy data we need from live environment into simulated environment
        data_copy_error = candle_util.init_simulation_data(live_env=live_env,
                                                           sim_env=sim_env,
                                                           symbols=[symbol],
                                                           days=9,
                                                           end_date=check_moment.date(),
                                                           model_feeder=ModelFeeder(sim_env),
                                                           skip_last_day_training=True)
        if data_copy_error is not None:
            live_env.warn_process(data_copy_error)
            return Breakout1SetupData._blank_breakout1_setup_data(symbol=symbol,
                                                                  check_moment=check_moment,
                                                                  last_updated=live_env.time().now())

        # Create a Breakout1Model so we can test viability
        model = Breakout1Model(env=sim_env, model_type=AnalysisModelType.BREAKOUT1_MODEL)
        model_data = model.calculate_output(symbol)

        # Return the price graph data in a neat object
        day_minute_candles = aggregate_minute_candles(
            sim_env.mongo().load_symbol_day(symbol=symbol, day=check_moment.date()).candles)
        live_env.info_process('Generated breakout1 setup visual')
        return Breakout1SetupData(symbol=symbol,
                                  check_moment=check_moment,
                                  day_data=[candle.to_json() for candle in day_minute_candles],
                                  model_data=model_data.to_json(),
                                  last_updated=live_env.time().now())

    @classmethod
    def _blank_breakout1_setup_data(cls, symbol: str,
                                    check_moment: datetime,
                                    last_updated: datetime) -> 'Breakout1SetupData':
        """Returns a blank Breakout1ModelOutput (used when the simulation cannot be started)."""
        return Breakout1SetupData(symbol=symbol,
                                  check_moment=check_moment,
                                  day_data=[],
                                  model_data=Breakout1ModelOutput(day_date=check_moment.date()).to_json(),
                                  last_updated=last_updated)
