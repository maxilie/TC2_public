from datetime import date
from typing import Optional


class HealthChecker:
    """
    A manager containing methods that perform health checks on the program and its data.

    This is located under the webpanel package instead of tc2 because it could potentially access
    tc2 modules and create circular imports.

    All modules under the tc2 package must be imported locally into the perform_check method!
    """

    # noinspection PyUnresolvedReferences
    @staticmethod
    def perform_check(program: 'TC2Program',
                      live_env: 'ExecEnv',
                      sim_env: 'ExecEnv',
                      check_type: 'HealthCheckType',
                      symbol: Optional[str] = None,
                      day_date: Optional[date] = None) -> 'HealthCheckResult':
        """Tries to perform a health check, and returns the result (a pass/fail status and output msgs)."""

        # Import tc2 modules locally so they can be reloaded
        from tc2.TC2Program import TC2Program
        from tc2.health_checking.HealthCheckType import HealthCheckType
        program: TC2Program = program

        # Perform the health check
        if check_type is HealthCheckType.ALPACA:
            from tc2.health_checking.health_check.AlpacaCheck import AlpacaCheck
            return AlpacaCheck(
                env=live_env,
                sim_env=sim_env).run(program.account)

        elif check_type is HealthCheckType.MODEL_FEEDING:
            from tc2.health_checking.health_check.ModelFeedingCheck import ModelFeedingCheck
            return ModelFeedingCheck(
                env=live_env,
                sim_env=sim_env).run()

        elif check_type is HealthCheckType.DATA:
            from tc2.health_checking.health_check.DataCheck import DataCheck
            return DataCheck(
                env=live_env,
                sim_env=sim_env).run(symbol=symbol)

        elif check_type is HealthCheckType.DIP45:
            from tc2.health_checking.health_check.Dip45Check import Dip45Check
            return Dip45Check(
                env=live_env,
                sim_env=sim_env).run()

        elif check_type is HealthCheckType.MONGO:
            from tc2.health_checking.health_check.MongoCheck import MongoCheck
            return MongoCheck(
                env=live_env,
                sim_env=sim_env).run()

        elif check_type is HealthCheckType.POLYGON:
            from tc2.health_checking.health_check.PolygonCheck import PolygonCheck
            # noinspection PyTypeChecker
            return PolygonCheck(
                env=live_env,
                sim_env=sim_env).run()

        elif check_type is HealthCheckType.SIM_OUTPUT:
            from tc2.health_checking.health_check.SimOutputCheck import SimOutputCheck
            return SimOutputCheck(
                env=live_env,
                sim_env=sim_env).run(day_date)

        elif check_type is HealthCheckType.SIM_TIMINGS:
            from tc2.health_checking.health_check.SimTimingsCheck import SimTimingsCheck
            return SimTimingsCheck(
                env=live_env,
                sim_env=sim_env).run()

        else:
            error_msg = 'HealthChecker encountered a HealthCheckType which it doesn\'t know how to handle. ' \
                        'Likely another \'if\' statement is needed for unhandled check_type: {}' \
                .format(check_type.value)
            program.error_main(error_msg)
            raise ValueError(error_msg)
