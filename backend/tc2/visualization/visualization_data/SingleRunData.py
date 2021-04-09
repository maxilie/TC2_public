import json
from datetime import date, datetime, timedelta
from typing import Optional, Dict

from tc2.env.ExecEnv import ExecEnv
from tc2.strategy.execution.StrategyRun import StrategyRun
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.util.date_util import DATE_FORMAT, DATE_TIME_FORMAT
from tc2.util.market_util import OPEN_TIME, CLOSE_TIME
from tc2.visualization.VisualType import VisualType
from tc2.visualization.visualization_data.AbstractVisualizationData import AbstractVisualizationData


class SingleRunData(AbstractVisualizationData):
    """Contains the variables required to create a run graph visual page using the html template."""

    run_date: date
    profit: Optional[float]
    run_and_price_data: str

    def __init__(self, run_date: date, profit: Optional[float], run_and_price_data: str) -> None:
        super().__init__(VisualType.SINGLE_RUN)
        self.run_date = run_date
        self.profit = profit
        self.run_and_price_data = run_and_price_data

    def get_id(self) -> str:
        return self.visual_type.value + self.run_date.strftime(DATE_FORMAT)

    def to_json(self) -> Dict[str, any]:
        return {'run_graph_data': self.run_and_price_data,
                'run_date': self.run_date,
                'run_result': 'failed to enter' if self.profit is None else '{}% profit'.format(
                    '%.2f'.format(self.profit))}

    @classmethod
    def generate_data(cls, live_env: ExecEnv,
                      sim_env: ExecEnv,
                      **kwargs) -> 'SingleRunData':
        """
        Combines price history with a StrategyRun so we can overlay entry/exit points on the price graph.
        Returns a single-use SingleRunData object. Not meant to be stored in Redis.
        :keyword: run: StrategyRun
        :keyword: symbol_day: SymbolDay
        """

        # Extract parameters
        run: StrategyRun = kwargs['run']
        symbol_day: SymbolDay = kwargs['symbol_day']

        json_array = []

        # Calculate run info
        profit = None if run.sell_price is None else (run.sell_price - run.buy_price) / run.buy_price

        # Create a data point for each second
        moment = datetime.combine(symbol_day.day_date, OPEN_TIME)
        while moment < datetime.combine(symbol_day.day_date, CLOSE_TIME):
            # Ensure valid data is present for the second
            candle = symbol_day.get_candle_at_sec(moment)
            if candle is None:
                moment = moment + timedelta(seconds=1)
                continue

            # Create a data point for the second
            data_point = {
                "price": str(candle.open),
                "start_time": run.start_time.strftime(DATE_TIME_FORMAT),
                "buy_time": None if run.buy_time is None else run.buy_time.strftime(DATE_TIME_FORMAT),
                "end_time": None if run.end_time is None else run.end_time.strftime(DATE_TIME_FORMAT),
                "buy_price": None if run.buy_price is None else str(run.buy_price),
                "sell_price": None if run.sell_price is None else str(run.sell_price),
                "profit": str(profit)
            }

            # Save and move on to the next second
            json_array.append(data_point)
            moment = moment + timedelta(seconds=1)

        return SingleRunData(
            run_date=symbol_day.day_date,
            profit=profit,
            run_and_price_data=json.dumps(json_array))
