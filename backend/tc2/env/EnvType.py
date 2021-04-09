from enum import Enum


class EnvType(Enum):
    """
    The list of abstractable environments (for data, logging, and time) in which code can be run.
    This enables the same code to be simulated historically, run live, run as a unit test,
    or run in a simulated environment meant to optimize the live environment.
    """
    LIVE = 'LIVE'
    SIMULATION = 'SIMULATION'
    STARTUP_DEBUG_1 = 'STARTUP_DEBUG_1'
    STARTUP_DEBUG_2 = 'STARTUP_DEBUG_2'
    HEALTH_CHECKING = 'HEALTH_CHECKING'
    VISUAL_GENERATION = 'VISUAL_GENERATION'
    OPTIMIZATION = 'OPTIMIZATION'
