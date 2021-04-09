from typing import Optional

from tc2.data.data_storage.redis.workers.AbstractRedisWorker import AbstractRedisWorker


class RedisSettingsWorker(AbstractRedisWorker):
    """
    Contains functionality for saving and loading program settings.
    """

    def set_setting(self,
                    setting_name: str,
                    setting_value: str) -> None:
        """Saves the setting key,val pair."""
        self.client.hset('SETTING', setting_name, setting_value)

    def get_setting(self,
                    setting_name: str) -> Optional[str]:
        """Returns the setting's value, or None."""
        setting_str = self.client.hget('SETTING', setting_name)
        return setting_str.decode("utf-8") if setting_str is not None and len(setting_str) != 0 else None
