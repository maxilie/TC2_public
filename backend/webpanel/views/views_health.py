import traceback
from datetime import datetime
from threading import Thread
from typing import List, Union, Dict, Optional

from django.http import QueryDict
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from webpanel import shared, api_util
from webpanel.health_checking.HealthChecker import HealthChecker

"""
Handles API requests on the /api/health_checks endpoint.
"""


@api_view(['GET'])
def get_check_result(request):
    """
    Fetches the result of the specified health check from redis and returns it.
    """
    from tc2.health_checking.HealthCheckType import HealthCheckType

    # Get and validate parameters from the request.
    try:
        params = _get_params(request.GET)
    except Exception as e:
        return Response('Error parsing request parameters: {}'.format(e.args),
                        status=status.HTTP_400_BAD_REQUEST)
    if type(params) is Response:
        return params
    check_type: HealthCheckType = params[0]
    kwargs: Dict[str, any] = params[1]

    # Fetch the program instance.
    from tc2.TC2Program import TC2Program
    program: TC2Program = shared.program

    # Fetch the data from redis.
    try:
        # Fork the live environment so it can run in this thread.
        live_env = api_util.fork_live_env()

        # Load the health check.
        health_check_data = live_env.redis().load_health_check_result(check_type=check_type,
                                                                      check_params=kwargs)

        if health_check_data is None:
            return Response('You must perform this health check before getting its result',
                            status=status.HTTP_204_NO_CONTENT)

        return Response(health_check_data.to_json())
    except Exception:
        api_util.log_stacktrace('fetching health check data', traceback.format_exc())
        return Response('Error fetching health check data',
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def perform_check(request) -> Response:
    """
    Tries to perform a health check off-thread, print its output, and store it in redis.
    Returns a message indicating status: invalid request parameters, program busy, error, or success.
    """
    from tc2.health_checking.HealthCheckType import HealthCheckType

    # Get and validate parameters from the request.
    try:
        params = _get_params(request.GET)
    except Exception as e:
        return Response('Error parsing request parameters: {}'.format(e.args),
                        status=status.HTTP_400_BAD_REQUEST)
    if type(params) is Response:
        return params
    check_type: HealthCheckType = params[0]
    kwargs: Dict[str, any] = params[1]

    # Ensure that the program isn't already performing another check.
    if shared.program_checking_health.value:
        return Response('Already busy performing a health check',
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Fetch the program instance.
    from tc2.TC2Program import TC2Program
    program: TC2Program = shared.program

    # Run the health check in another thread.
    shared.program_checking_health.value = True

    def perform_check_logic():
        try:
            # Fork the live environment so it can run in this thread.
            live_env = api_util.fork_live_env()

            # Create a simulated environment in case we need to run simulations in order to perform the health check.
            sim_env = api_util.fork_sim_env_health()

            # Perform check.
            result = HealthChecker.perform_check(program=program,
                                                 live_env=live_env,
                                                 sim_env=sim_env,
                                                 check_type=check_type,
                                                 **kwargs)

            # Save result in redis.
            live_env.redis().save_health_check_result(check_type=check_type,
                                                      check_params=kwargs,
                                                      result=result)

            # Unblock health checking operations.
            shared.program_checking_health.value = False
            shared.health_check_thread = None
        except Exception:
            api_util.log_stacktrace('running a health check', traceback.format_exc())
            shared.program_checking_health.value = False
            shared.health_check_thread = None

    shared.health_check_thread = Thread(target=perform_check_logic)
    shared.health_check_thread.start()

    return Response(f'Started {check_type.value.lower()} check off-thread. The new output will be available soon.')


def _get_params(req: QueryDict) -> Union[Response, List[any]]:
    """
    Parses the request for health check parameters.
    If successful, returns a list with two elements:
      - the HealthCheckType, and
      - a dictionary of parameters specific to the check
    If unsuccessful, returns a Response saying why the request was invalid.
    """
    from tc2.health_checking.HealthCheckType import HealthCheckType
    from tc2.util.date_util import DATE_FORMAT

    # Get health check from request parameters.
    check_type = _string_param(req, 'check_type')
    if check_type is not None:
        check_type = HealthCheckType[check_type.upper()]
    if check_type is None:
        return Response('Parameter \'check_type\' is invalid or not specified',
                        status=status.HTTP_400_BAD_REQUEST)

    # Get additional parameter(s) specific to the health check.
    kwargs = {}

    symbol_str = _string_param(req, 'symbol')
    day_date_str = _string_param(req, 'day_date')

    # Get parameters specific to DATA check.
    if check_type is HealthCheckType.DATA and symbol_str is not None:
        kwargs['symbol'] = symbol_str

    # Get parameters specific to SIMULATION_OUTPUT check.
    if check_type is HealthCheckType.SIM_OUTPUT:
        if day_date_str is not None and datetime.strptime(day_date_str, DATE_FORMAT) is not None:
            kwargs['day_date'] = datetime.strptime(day_date_str, DATE_FORMAT)
        else:
            return Response('Parameter \'day_date\' is missing/invalid',
                            status=status.HTTP_400_BAD_REQUEST)

    # Return the parameters.
    return [check_type, kwargs]


def _string_param(req: QueryDict, param: str) -> Optional[str]:
    """
    Extracts a string parameter value, or None, from the GET request.
    """
    return req.get(param) if req.get(param, None) is not None else None
