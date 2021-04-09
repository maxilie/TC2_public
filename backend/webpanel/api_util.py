import re
import traceback
from datetime import datetime, date
from typing import Optional, List

from webpanel import shared


def log_stacktrace(action: str,
                   stacktrace: str) -> None:
    """
    Prints an error message to the API logfeed.
    """
    from webpanel.shared import program
    from tc2.log.LogFeed import LogLevel
    program.logfeed_api.log(LogLevel.ERROR, f'Error {action}:')
    program.logfeed_api.log(LogLevel.WARNING, stacktrace)


def fork_live_env(logfeed_process: Optional['LogFeed'] = None) -> 'ExecEnv':
    """
    Returns an execution environment that outputs its logs to the API logfeed and can be used by the calling thread.
    """
    from tc2.env.ExecEnv import ExecEnv

    if not logfeed_process:
        logfeed_process = shared.program.logfeed_api

    live_env = ExecEnv(shared.program.logfeed_program, logfeed_process, creator_env=shared.program.live_env)
    live_env.fork_new_thread()
    return live_env


def fork_sim_env_health() -> 'ExecEnv':
    """
    Returns an execution environment of type HEALTH_CHECKING that can be used by the calling thread.
    """
    from tc2.env.ExecEnv import ExecEnv
    from tc2.env.EnvType import EnvType
    from tc2.env.TimeEnv import TimeEnv
    from tc2.data.data_storage.redis.RedisManager import RedisManager
    from tc2.data.data_storage.mongo.MongoManager import MongoManager
    from tc2.data.stock_data_collection.PolygonDataCollector import PolygonDataCollector

    if shared.sim_env_health is None:
        shared.sim_env_health = ExecEnv(None, None)
        sim_time = TimeEnv(datetime.now())
        shared.sim_env_health.setup_first_time(env_type=EnvType.HEALTH_CHECKING,
                                               time=sim_time,
                                               data_collector=PolygonDataCollector(
                                                   logfeed_program=None,
                                                   logfeed_process=None,
                                                   time_env=sim_time
                                               ),
                                               mongo=MongoManager(None, EnvType.HEALTH_CHECKING),
                                               redis=RedisManager(None, EnvType.HEALTH_CHECKING))
        return shared.sim_env_health

    # Wipe databases
    shared.sim_env_visuals.reset_dbs()

    shared.sim_env_health.fork_new_thread(creator_env=shared.sim_env_health)
    return shared.sim_env_health


def fork_sim_env_visuals() -> 'ExecEnv':
    """
    Returns an execution environment of type VISUALS_GENERATION that can be used by the calling thread.
    """
    from tc2.env.ExecEnv import ExecEnv
    from tc2.env.EnvType import EnvType
    from tc2.env.TimeEnv import TimeEnv
    from tc2.data.data_storage.redis.RedisManager import RedisManager
    from tc2.data.data_storage.mongo.MongoManager import MongoManager
    from tc2.data.stock_data_collection.PolygonDataCollector import PolygonDataCollector

    if shared.sim_env_visuals is None:
        shared.sim_env_visuals = ExecEnv(shared.program.logfeed_program, shared.program.logfeed_visuals)
        sim_time = TimeEnv(datetime.now())
        shared.sim_env_visuals.setup_first_time(env_type=EnvType.VISUAL_GENERATION,
                                                time=sim_time,
                                                data_collector=PolygonDataCollector(
                                                    logfeed_program=shared.program.logfeed_program,
                                                    logfeed_process=shared.program.logfeed_visuals,
                                                    time_env=sim_time
                                                ),
                                                mongo=MongoManager(shared.program.logfeed_visuals,
                                                                   EnvType.VISUAL_GENERATION),
                                                redis=RedisManager(shared.program.logfeed_visuals,
                                                                   EnvType.VISUAL_GENERATION))
        return shared.sim_env_visuals

    # Wipe databases
    shared.sim_env_visuals.reset_dbs()

    shared.sim_env_visuals.fork_new_thread(creator_env=shared.sim_env_visuals)
    return shared.sim_env_visuals


def fork_sim_env_simulations() -> 'ExecEnv':
    """
    Returns an execution environment of type SIMULATION that can be used by the calling thread.
    """
    from tc2.env.ExecEnv import ExecEnv
    from tc2.env.EnvType import EnvType
    from tc2.env.TimeEnv import TimeEnv
    from tc2.data.data_storage.redis.RedisManager import RedisManager
    from tc2.data.data_storage.mongo.MongoManager import MongoManager
    from tc2.data.stock_data_collection.PolygonDataCollector import PolygonDataCollector

    if shared.sim_env_visuals is None:
        shared.sim_env_simulations = ExecEnv(shared.program.logfeed_program, shared.program.logfeed_api)
        sim_time = TimeEnv(datetime.now())
        shared.sim_env_simulations.setup_first_time(env_type=EnvType.SIMULATION,
                                                    time=sim_time,
                                                    data_collector=PolygonDataCollector(
                                                        logfeed_program=shared.program.logfeed_program,
                                                        logfeed_process=shared.program.logfeed_api,
                                                        time_env=sim_time
                                                    ),
                                                    mongo=MongoManager(shared.program.logfeed_api,
                                                                       EnvType.SIMULATION),
                                                    redis=RedisManager(shared.program.logfeed_api,
                                                                       EnvType.SIMULATION))
        return shared.sim_env_simulations

    # Wipe databases
    shared.sim_env_simulations.reset_dbs()

    shared.sim_env_visuals.fork_new_thread(creator_env=shared.sim_env_simulations)
    return shared.sim_env_simulations


url_encode_mappings = {
    '%': '%25',
    '!': '%21',
    '@': '%40',
    '#': '%23',
    '$': '%24',
    '&': '%26',
    '*': '%2A',
    '(': '%28',
    ')': '%29',
    '=': '%3D',
    ':': '%3A',
    '/': '%2F',
    ',': '%2C',
    ';': '%3B',
    '?': '%3F',
    '+': '%2B',
    "'": '%27',
}

url_encode_exp = re.compile("|".join(map(re.escape, url_encode_mappings.keys())))


def url_encode(plain_str: str) -> str:
    """
    "Percent escapes" all reserved characters (/!*[? etc.).
    Logs an error if special characters (reserved chars plus A-z0-9-_.~) are present.
    """
    if re.search(r'[^!@#$&*()=:/,;?+\'A-z0-9\-_.~]', plain_str):
        print(f'Tried to url-encode a string that contains problematic characters: {plain_str}')

    return url_encode_exp.sub(lambda match: url_encode_mappings[match.group(0)], plain_str)


url_decode_mappings = {
    '%25': '%',
    '%21': '!',
    '%40': '@',
    '%23': '#',
    '%24': '$',
    '%26': '&',
    '%2A': '*',
    '%28': '(',
    '%29': ')',
    '%3D': '=',
    '%3A': ':',
    '%2F': '/',
    '%2C': ',',
    '%3B': ';',
    '%3F': '?',
    '%2B': '+',
    '%27': "'",
}

url_decode_exp = re.compile("|".join(map(re.escape, url_decode_mappings.keys())))


def url_decode(url_str: str) -> str:
    """
    Decodes a string that was url encoded by the logic of api_util.url_encode().
    Logs an error if non-encoded characters (not %A-z0-9-_.~) are present.
    """
    if re.search(r'[^A-z0-9\-_.]', url_str):
        print(f'Tried to url-decode a string that contains problematic characters: {url_str}')

    try:
        return url_encode_exp.sub(lambda match: url_decode_mappings[match.group(0)], url_str)
    except Exception as e:
        log_stacktrace('url-decoding string (program will assume it was already decoded)', traceback.format_exc())
        return url_str


def parse_param_str(request, param) -> Optional[str]:
    """
    Parses the GET request for the string-valued parameter, or None.
    """
    return url_decode(request.GET[param]) if param in request.GET else None


def parse_param_int(request, param) -> Optional[int]:
    """
    Parses the GET request for the integer-valued parameter, or None.
    """
    data_str = parse_param_str(request, param)
    if data_str is None:
        return None
    try:
        return int(data_str)
    except ValueError:
        return None


def parse_param_date(request, param) -> Optional[date]:
    """
    Parses the GET request for the date-valued parameter, or None.
    """
    from tc2.util.date_util import DATE_FORMAT
    data_str = parse_param_str(request, param)
    if data_str is None:
        return None
    try:
        return datetime.strptime(data_str, DATE_FORMAT).date()
    except ValueError:
        return None


def parse_param_datetime(request, param) -> Optional[datetime]:
    """
    Parses the GET request for the datetime-valued parameter, or None.
    """
    from tc2.util.date_util import DATE_TIME_FORMAT
    data_str = parse_param_str(request, param)
    if data_str is None:
        return None
    try:
        return datetime.strptime(data_str, DATE_TIME_FORMAT)
    except ValueError:
        return None


def parse_param_str_list(request, param, list_splitter: str = ',') -> Optional[List[str]]:
    """
    Parses the GET request for the list-valued parameter, or None.
    """
    data_str = parse_param_str(request, param)
    if data_str is None:
        return None
    return data_str.split(list_splitter) if list_splitter in data_str else [data_str]
