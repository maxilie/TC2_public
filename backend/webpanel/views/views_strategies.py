import traceback
from threading import Thread

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from webpanel import api_util, shared

"""
Contains methods to handle api requests on the /api/strategy endpoint.
These methods are for controlling data collection.
"""


@api_view(['GET'])
def get_day_strategies(request):
    """
    Returns a list of day trading strategy ids.
    """
    try:
        from tc2.util.strategy_constants import DAY_STRATEGY_IDS
        return Response(DAY_STRATEGY_IDS)
    except Exception as e:
        api_util.log_stacktrace('getting day-trading strategy ids', traceback.format_exc())
        return Response('Error getting day-trading strategy ids!',
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_swing_strategies(request):
    """
    Returns a list of swing trading strategy ids.
    """
    try:
        from tc2.util.strategy_constants import SWING_STRATEGY_IDS
        return Response(SWING_STRATEGY_IDS)
    except Exception as e:
        api_util.log_stacktrace('getting swing-trading strategy ids', traceback.format_exc())
        return Response('Error getting swing-trading strategy ids!',
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def is_running_simulation(request):
    """
    Returns True if the program is running a user-initiated simulation.
    """
    return Response('true') if shared.running_panel_simulation.value else Response('false')


@api_view(['GET'])
def simulate_day_strategy(request):
    """
    Runs a simulation of a day-trading strategy.
    """
    from tc2.strategy.execution.simulated.StrategySimulator import StrategySimulator
    from webpanel import shared
    from tc2.util.strategy_constants import DAY_STRATEGY_CLASSES

    # Get parameters.
    symbol = api_util.parse_param_str(request, 'symbol')
    strategy_id = api_util.parse_param_str(request, 'strategy_id')
    start_moment = api_util.parse_param_datetime(request, 'moment')
    warmup_days = api_util.parse_param_int(request, 'warmup_days')

    # Validate parameters.
    if symbol is None or strategy_id is None or start_moment is None or warmup_days is None:
        return Response('Invalid parameters',
                        status=status.HTTP_400_BAD_REQUEST)

    # Check that a simulation isn't already running.
    if shared.running_panel_simulation.value:
        return Response('Already performing a simulation',
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Mark program as busy running a simulation.
    shared.running_panel_simulation.value = True

    # Define simulation logic.
    def run_simulation():
        try:
            # Fork the live environment so it can run in this thread.
            live_env = api_util.fork_live_env(logfeed_process=shared.program.logfeed_api)

            # Remove the output of the last simulation.
            live_env.redis().clear_simulation_output()

            # Create a virtual environment in which to run the simulation.
            sim_env = api_util.fork_sim_env_simulations()
            sim_env.time().set_moment(start_moment)

            # Create a strategy.
            strategy_cls = None
            for strat_cls in DAY_STRATEGY_CLASSES:
                if strat_cls.get_id() == strategy_id:
                    strategy_cls = strat_cls

            if strategy_cls is None:
                sim_env.error_process(f'Could not find strategy with id "{strategy_id}"')
            strategy = strategy_cls(env=sim_env,
                                    symbols=[symbol])

            # Run the simulation.
            simulator = StrategySimulator(strategy=strategy,
                                          live_env=live_env)
            simulator.run(warmup_days=warmup_days)
            sim_env.info_process(f'Completed {strategy.get_id()} simulation. '
                                 f'Results: {strategy.run_info.to_json()}')

            # Save the output of this simulation.
            live_env.redis().save_simulation_output(strategy.run_info.to_json())

            # Mark program as ready to run another simulation.
            shared.running_panel_simulation.value = False
            shared.simulations_thread = None
        except Exception as e:
            traceback.print_exc()
            shared.running_panel_simulation.value = False
            shared.simulations_thread = None

    # Run simulation logic in another thread.
    shared.simulations_thread = Thread(target=run_simulation)
    shared.simulations_thread.start()

    return Response('Started simulation in another thread. Check API logfeed.')
