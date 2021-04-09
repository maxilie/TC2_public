import pickle
from typing import Dict, Optional

from tc2.data.data_storage.redis.workers.AbstractRedisWorker import AbstractRedisWorker
from tc2.visualization.VisualType import VisualType


class RedisVisualsWorker(AbstractRedisWorker):
    """
    Contains functionality for saving and loading visuals data.
    """

    def save_visual_data(self, visual_type: VisualType,
                         visual_params: Dict[str, any],
                         data: 'AbstractVisualizationData') -> None:
        """
        Serializes and saves the result of the health check.
        """
        self.client.hset(self.get_prefix() + 'VISUAL-DATA',
                         visual_type.value + '_' +
                         '_'.join([f'{key}:{str(val)}' for key, val in visual_params.items()]),
                         pickle.dumps(data))

    def load_visual_data(self, visual_type: VisualType,
                         visual_params: Dict[str, any]) -> Optional['AbstractVisualizationData']:
        """
        :return: a HealthCheckResult object for the symbol, or None
        """
        data_str = self.client.hget(self.get_prefix() + 'VISUAL-DATA',
                                    visual_type.value + '_' +
                                    '_'.join([f'{key}:{str(val)}' for key, val in visual_params.items()]))
        if data_str is None or len(data_str) == 0:
            return None
        else:
            return pickle.loads(data_str)
