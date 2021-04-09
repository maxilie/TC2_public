import multiprocessing
from ctypes import c_bool
from threading import Thread
from typing import Optional

# The main program to be accessed by django worker threads
program: Optional['TC2Program'] = None

# noinspection PyTypeChecker
program_starting = multiprocessing.Value(c_bool, False)
# noinspection PyTypeChecker
data_busy = multiprocessing.Value(c_bool, False)
# noinspection PyTypeChecker
patching_data = multiprocessing.Value(c_bool, False)
# noinspection PyTypeChecker
healing_data = multiprocessing.Value(c_bool, False)
# noinspection PyTypeChecker
program_checking_health = multiprocessing.Value(c_bool, False)
# noinspection PyTypeChecker
program_updating_visual = multiprocessing.Value(c_bool, False)
# noinspection PyTypeChecker
running_panel_simulation = multiprocessing.Value(c_bool, False)

# Thread that performs (resource-intensive) health checking
health_check_thread: Optional[Thread] = None

# Environment for running a health check
sim_env_health: Optional['ExecEnv'] = None

# Thread that performs (resource-intensive) visual generation
visuals_thread: Optional[Thread] = None

# Environment for generating visuals
sim_env_visuals: Optional['ExecEnv'] = None

# Thread that performs (resource-intensive) strategy simulation
simulations_thread: Optional[Thread] = None

# Environment for running simulations
sim_env_simulations: Optional['ExecEnv'] = None
