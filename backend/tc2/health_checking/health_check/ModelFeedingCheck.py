from tc2.health_checking.health_check.AbstractHealthCheck import AbstractHealthCheck
from tc2.health_checking.HealthCheckResult import HealthCheckResult


class ModelFeedingCheck(AbstractHealthCheck):
    """
    Not meant to be accessed except by HealthChecker.
    Checks that daily data collection and model feeding work as expected within a simulated environment.

    Conditions for success:
    + TODO Data needed for simulated model feeding is present.
    + TODO Expected data is saved after model feeding.
    + TODO Certain models have reasonable output after model feeding.
    """

    def run(self) -> HealthCheckResult:
        # TODO Use self.test_data_env to trigger simulated daily collection

        return self.make_result()
