from datetime import date, datetime, time

from tc2.data.data_storage.mongo.MongoManager import MongoManager
from tc2.data.data_storage.redis.RedisManager import RedisManager
from tc2.data.stock_data_collection.PolygonDataCollector import PolygonDataCollector
from tc2.env.EnvType import EnvType
from tc2.env.ExecEnv import ExecEnv
from tc2.env.TimeEnv import TimeEnv
from tc2.log.LogFeed import LogLevel
from tc2.startup_task.AbstractStartupTask import AbstractStartupTask
from tc2.strategy.execution.simulated.StrategySimulator import StrategySimulator
from tc2.strategy.strategies.long_short.LongShortStrategy import LongShortStrategy


class DebugSimulationTask(AbstractStartupTask):
    """
    STARTUP TASK (single-run): run a simulation of LongShortStrategy.
    """

    def run(self) -> None:
        self.program.logfeed_program.log(LogLevel.INFO, 'Debug task setting up simulation environment')

        # Set simulation parameters.
        day_date = date(year=2020, month=3, day=10)

        # Clone live environment so it can run on this thread.
        live_env = ExecEnv(self.program.logfeed_program, self.program.logfeed_program, self.program.live_env)
        live_env.fork_new_thread()

        # Initialize simulation environment.
        sim_time_env = TimeEnv(datetime.combine(day_date, time(hour=11, minute=3, second=40)))
        sim_data_collector = PolygonDataCollector(logfeed_program=self.program.logfeed_program,
                                                  logfeed_process=self.program.logfeed_program,
                                                  time_env=sim_time_env)
        sim_redis = RedisManager(self.program.logfeed_program, EnvType.STARTUP_DEBUG_1)
        sim_mongo = MongoManager(self.program.logfeed_program, EnvType.STARTUP_DEBUG_1)
        sim_env = ExecEnv(self.program.logfeed_program, self.program.logfeed_program)
        sim_env.setup_first_time(env_type=EnvType.STARTUP_DEBUG_1,
                                 time=sim_time_env,
                                 data_collector=sim_data_collector,
                                 mongo=sim_mongo,
                                 redis=sim_redis)

        # Place the strategy in a simulated environment.
        strategy = LongShortStrategy(env=sim_env,
                                     symbols=['SPY', 'SPXL', 'SPXS'])

        # Simulate the strategy so its output gets printed to logfeed_optimization.
        self.program.logfeed_program.log(LogLevel.INFO, 'Creating StrategySimulator for debug task')
        simulator = StrategySimulator(strategy, live_env, all_symbols=['SPY', 'SPXL', 'SPXS'])
        self.program.logfeed_program.log(LogLevel.INFO, 'Running simulation of LongShortStrategy')
        simulator.run(warmup_days=2)
        self.program.logfeed_program.log(LogLevel.INFO, f'Completed LongShortStrategy simulation. '
                                                f'Results: {strategy.run_info.to_json()}')
