from typing import Dict

from tc2.env.ExecEnv import ExecEnv
from tc2.visualization.VisualType import VisualType


class AbstractVisualizationData:
    visual_type: VisualType

    def __init__(self, visual_type: VisualType):
        self.visual_type = visual_type

    def to_json(self) -> Dict[str, any]:
        """
        :return: a dictionary to be passed into the browser and used to display the visual
        """
        raise NotImplementedError

    def get_id(self) -> str:
        """
        :return: a string identifier for this specific visual (e.g. 'PRICE_GRAPH_AAPL_2020/01/02')
        """
        raise NotImplementedError

    @classmethod
    def generate_data(cls, live_env: ExecEnv,
                      sim_env: ExecEnv,
                      **kwargs) -> 'AbstractVisualizationData':
        """
        Compiles the visual's data and returns it in a VisualizationData object.
        :param live_env: a LIVE execution environment that can be accessed by this thread
        :param sim_env: a VISUALIZATION environment with no data
        """
        raise NotImplementedError
