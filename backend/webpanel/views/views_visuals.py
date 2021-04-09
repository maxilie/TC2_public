import traceback
from datetime import datetime
from threading import Thread
from typing import Union, List, Dict, Optional

from django.http import QueryDict
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from webpanel import shared, api_util

"""
Handles API requests on the /api/visuals endpoint.
"""


@api_view(['GET'])
def get_visual_data(request):
    """Fetches and returns data from redis that is needed to display the specified visual."""
    from tc2.visualization.VisualType import VisualType

    # Get and validate parameters from the request
    try:
        params = _get_params(request.GET)
    except Exception as e:
        return Response('Error parsing request parameters: {}'.format(e.args),
                        status=status.HTTP_400_BAD_REQUEST)
    if type(params) is Response:
        return params
    visual_type: VisualType = params[0]
    kwargs: Dict[str, any] = params[1]

    # Fetch the data from redis
    try:
        # Fork the live environment so it can run in this thread
        live_env = api_util.fork_live_env(logfeed_process=shared.program.logfeed_visuals)

        # Load the visual's data from redis
        visual_data = live_env.redis().load_visual_data(visual_type=visual_type,
                                                        visual_params=kwargs)

        if visual_data is None:
            return Response('You must generate this visual\'s data before getting its result',
                            status=status.HTTP_204_NO_CONTENT)

        return Response(visual_data.to_json())
    except Exception:
        api_util.log_stacktrace('fetching visual data', traceback.format_exc())
        return Response('Error fetching visual data',
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def generate_visual(request) -> Response:
    """
    Tries to update data needed for a visual and store the new result.
    Returns a message indicating status: invalid request parameters, program busy, error, or success.
    """
    from webpanel.visuals_generation.VisualsGenerator import VisualsGenerator
    from tc2.visualization.VisualType import VisualType
    from tc2.TC2Program import TC2Program

    # Get and validate parameters from the request
    try:
        params = _get_params(request.GET)
    except Exception as e:
        return Response('Error parsing request parameters: {}'.format(e.args),
                        status=status.HTTP_400_BAD_REQUEST)
    if type(params) is Response:
        return params
    visual_type: VisualType = params[0]
    kwargs: Dict[str, any] = params[1]

    # Ensure that the program isn't already performing another check
    if shared.program_updating_visual.value:
        return Response('Already busy updating a visual',
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Fetch the program instance
    program: TC2Program = shared.program

    # Update the visual in another thread
    shared.program_updating_visual.value = True

    def perform_check_logic():
        try:
            # Fork the live environment so it can run in this thread
            live_env = api_util.fork_live_env(logfeed_process=shared.program.logfeed_visuals)

            # Create a simulated environment in case we need to run simulations in order to generate the visual
            sim_env = api_util.fork_sim_env_visuals()

            # Generate visual
            visual_data = VisualsGenerator.generate_visual(program=program,
                                                           live_env=live_env,
                                                           sim_env=sim_env,
                                                           visual_type=visual_type,
                                                           **kwargs)

            # Save visual's data in redis
            live_env.redis().save_visual_data(visual_type=visual_type,
                                              visual_params=kwargs,
                                              data=visual_data)

            # Unblock health checking operations
            shared.program_updating_visual.value = False
            shared.visuals_thread = None
        except Exception:
            api_util.log_stacktrace('generating visual data', traceback.format_exc())
            shared.program_updating_visual.value = False
            shared.visuals_thread = None

    shared.health_check_thread = Thread(target=perform_check_logic)
    shared.health_check_thread.start()

    return Response(f'Started {visual_type.value.lower()} data generation off-thread. '
                    'The new data will be available soon.')


def _get_params(req: QueryDict) -> Union[Response, List[any]]:
    """
    Parses the request for visual data parameters.
    If successful, returns a list with two elements:
      - the VisualType, and
      - a dictionary of parameters specific to the visual type
    If unsuccessful, returns a Response saying why the request was invalid.
    """
    from tc2.visualization.VisualType import VisualType
    from tc2.util.date_util import DATE_TIME_FORMAT

    # Get visual type from request parameters
    visual_type = _string_param(req, 'visual_type')
    if visual_type is not None:
        visual_type = VisualType[visual_type.upper()]
    if visual_type is None:
        return Response('Parameter \'visual_type\' is invalid or not specified',
                        status=status.HTTP_400_BAD_REQUEST)

    # Get additional parameter(s) specific to the visual
    kwargs = {}

    symbol_str = _string_param(req, 'symbol')
    day_date_str = _string_param(req, 'day_date')
    paper_str = _string_param(req, 'paper')
    check_moment_str = _string_param(req, 'check_moment')

    # Get parameters specific to PRICE_GRAPH visual
    if visual_type is VisualType.PRICE_GRAPH:
        if symbol_str is not None:
            kwargs['symbol'] = symbol_str.upper()
        else:
            return Response('Missing required parameter: \'symbol\'',
                            status=status.HTTP_400_BAD_REQUEST)

    # Get parameters specific to RUN_HISTORY visual
    if visual_type is VisualType.RUN_HISTORY:
        if paper_str is not None:
            kwargs['paper'] = True if paper_str.lower() == 'paper' else False
        else:
            return Response('Missing required parameter: \'paper\'',
                            status=status.HTTP_400_BAD_REQUEST)

    # Get parameters specific to SWING_SETUP visual
    if visual_type is VisualType.SWING_SETUP:
        if symbol_str is not None:
            kwargs['symbol'] = symbol_str.upper()
        else:
            return Response('Missing required parameter: \'symbol\'',
                            status=status.HTTP_400_BAD_REQUEST)

    # Get parameters specific to BREAKOUT1_SETUP visual
    if visual_type is VisualType.BREAKOUT1_SETUP:
        if symbol_str is not None:
            kwargs['symbol'] = symbol_str.upper()
        else:
            return Response('Missing required parameter: \'symbol\'',
                            status=status.HTTP_400_BAD_REQUEST)
        if check_moment_str is not None and datetime.strptime(check_moment_str, DATE_TIME_FORMAT) is not None:
            kwargs['check_moment'] = datetime.strptime(check_moment_str, DATE_TIME_FORMAT)
        else:
            return Response('Missing/invalid required parameter: \'check_moment\'',
                            status=status.HTTP_400_BAD_REQUEST)

    # Return the parameters
    return [visual_type, kwargs]


def _string_param(req: QueryDict, param: str) -> Optional[str]:
    """Extracts a string parameter value, or None, from the GET request."""
    return req.get(param) if req.get(param, None) is not None else None
