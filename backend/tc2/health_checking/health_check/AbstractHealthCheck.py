from typing import List

from tc2.env.ExecEnv import ExecEnv
from tc2.health_checking.HealthCheckResult import HealthCheckResult


class AbstractHealthCheck(ExecEnv):
    """
    The structure of a health check.
    + run():                runs the model_type and returns a HealthCheckResult
    + debug(msg):           records a debug message to give additional info on the model_type
    + set_passing(bool):    sets the model_type to True or False (passing or failing)
    + make_result():        returns the HealthCheckResult
    """

    sim_env: ExecEnv
    debug_messages: List[str]
    passing: bool

    def __init__(self, env: ExecEnv,
                 sim_env: ExecEnv) -> None:
        super().__init__(None, None)
        self.clone_same_thread(env)

        self.sim_env = sim_env
        self.debug_messages = ['Initializing health check']
        self.passing = False

    def run(self, **kwargs) -> HealthCheckResult:
        """Runs the health check and returns a HealthCheckResult."""
        raise NotImplementedError

    def debug(self, msg: str) -> None:
        """Records a debug message to give additional info on the model_type."""
        self.debug_messages.append(msg)

    def set_passing(self, passing: bool) -> None:
        """Marks the health check as passing or failing."""
        self.passing = passing

    def make_result(self) -> HealthCheckResult:
        """
        Meant to be called after adding messages with self.debug() and marking success/failure with self.set_passing().
        """
        return HealthCheckResult(self.passing, self.debug_messages, self.time().now())
