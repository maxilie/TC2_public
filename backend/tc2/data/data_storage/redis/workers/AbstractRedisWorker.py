from redis import Redis

from tc2.env.EnvType import EnvType
from tc2.log.LogFeed import LogFeed
from tc2.log.Loggable import Loggable


class AbstractRedisWorker(Loggable):
    """A class equipped with a redis client; used to perform a group of specific tasks."""

    client: Redis
    env_type: EnvType

    def __init__(self, logfeed_program: LogFeed, client: Redis, env_type: EnvType):
        # Route all logs to the main LogFeed
        super().__init__(logfeed_program=logfeed_program, logfeed_process=logfeed_program)

        self.client = client
        self.env_type = env_type

    def get_prefix(self) -> str:
        """
        Returns the string which identifies the info's data environment.
        All data stored in redis must be prefixed in order to distinguish it from other environment's data.
        """
        return self.env_type.value + '_'
