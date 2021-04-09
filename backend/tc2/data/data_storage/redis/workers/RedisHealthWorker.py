import pickle
from typing import Dict, Optional

from tc2.health_checking.HealthCheckResult import HealthCheckResult
from tc2.health_checking.HealthCheckType import HealthCheckType
from tc2.data.data_storage.redis.workers.AbstractRedisWorker import AbstractRedisWorker


class RedisHealthWorker(AbstractRedisWorker):
    """
    Contains functionality for saving and loading health check data.
    """

    def save_health_check_result(self, check_type: HealthCheckType, check_params: Dict[str, any],
                                 result: HealthCheckResult) -> None:
        """
        Serializes and saves the result of the health check.
        """
        self.client.hset(self.get_prefix() + 'HEALTH-DATA',
                         check_type.value + '_' + '_'.join([f'{key}:{str(val)}' for key, val in check_params.items()]),
                         pickle.dumps(result))

    def load_health_check_result(self, check_type: HealthCheckType,
                                 check_params: Dict[str, any]) -> Optional[HealthCheckResult]:
        """
        :return: a HealthCheckResult object for the symbol, or None
        """
        result_str = self.client.hget(self.get_prefix() + 'HEALTH-DATA',
                                      check_type.value + '_' +
                                      '_'.join([f'{key}:{str(val)}' for key, val in check_params.items()]))
        if result_str is None or len(result_str) == 0:
            return None
        else:
            return pickle.loads(result_str)
