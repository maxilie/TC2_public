from datetime import datetime
from typing import Dict, List

from tc2.env.ExecEnv import ExecEnv
from tc2.util.strategy_constants import DAY_STRATEGY_IDS
from tc2.util.date_util import DATE_TIME_FORMAT
from tc2.visualization.VisualType import VisualType
from tc2.visualization.visualization_data.AbstractVisualizationData import AbstractVisualizationData


class RunHistoryData(AbstractVisualizationData):
    """Contains the variables required to create a trade history chart."""

    # Ex. {{'buy_time': '2020/1/2_13:04:00', ...}, ...}
    runs_data: List[Dict]
    last_updated: datetime

    def __init__(self, runs_data: List[Dict],
                 last_updated: datetime) -> None:
        super().__init__(VisualType.RUN_HISTORY)
        self.runs_data = runs_data
        self.last_updated = last_updated

    def get_id(self) -> str:
        return str(self.visual_type.value)

    def to_json(self) -> Dict[str, any]:
        return {'runs_data': self.runs_data,
                'last_updated': self.last_updated.strftime(DATE_TIME_FORMAT)}

    @classmethod
    def generate_data(cls, live_env: ExecEnv,
                      sim_env: ExecEnv,
                      **kwargs) -> 'RunHistoryData':
        """
        Compiles the program's trade history into a json string usable by the visualization script.
        :keyword: paper
        """

        # Extract parameters
        paper: bool = kwargs['paper']

        # Load entire run history for the endpoint (live or paper)
        runs = live_env.redis().get_live_run_history(strategies=DAY_STRATEGY_IDS, paper=paper)

        # Return the trade data in a neat object
        return RunHistoryData(runs_data=[run.to_json() for run in runs],
                              last_updated=live_env.time().now())
