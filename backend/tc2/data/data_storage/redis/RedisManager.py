import os
import traceback
from datetime import datetime, date
from typing import List, Optional, Dict

from redis import Redis

from tc2.data.data_storage.redis.workers.RedisCandlesWorker import RedisCandlesWorker
from tc2.data.data_storage.redis.workers.RedisCollectionWorker import RedisCollectionWorker
from tc2.data.data_storage.redis.workers.RedisHealthWorker import RedisHealthWorker
from tc2.data.data_storage.redis.workers.RedisModelsWorker import RedisModelsWorker
from tc2.data.data_storage.redis.workers.RedisSettingsWorker import RedisSettingsWorker
from tc2.data.data_storage.redis.workers.RedisStrategiesWorker import RedisStrategiesWorker
from tc2.data.data_storage.redis.workers.RedisVisualsWorker import RedisVisualsWorker
from tc2.data.data_structs.account_data.RoundTripTrade import RoundTripTrade
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.env.EnvType import EnvType
from tc2.health_checking.HealthCheckResult import HealthCheckResult
from tc2.health_checking.HealthCheckType import HealthCheckType
from tc2.log.LogFeed import LogFeed
from tc2.log.Loggable import Loggable
from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.strategy.execution.StrategyRun import StrategyRun
from tc2.util.Config import BrokerEndpoint
from tc2.visualization.VisualType import VisualType


class RedisManager(Loggable):
    client: Redis
    env_type: EnvType
    _connected: bool
    _pid: int

    # Workers
    candles_worker: RedisCandlesWorker
    health_worker: RedisHealthWorker
    models_worker: RedisModelsWorker
    strategies_worker: RedisStrategiesWorker
    visuals_worker: RedisVisualsWorker
    collection_worker: RedisCollectionWorker
    settings_worker: RedisSettingsWorker

    def __init__(self,
                 logfeed_process: LogFeed,
                 env_type: EnvType) -> None:
        # Route all logs to the process's LogFeed.
        super().__init__(logfeed_program=logfeed_process, logfeed_process=logfeed_process)

        # Set config and environment.
        self.env_type = env_type
        self._connected = False
        self._pid = os.getpid()

    """
    Initialization...
    """

    def connect(self,
                ip: str,
                port: str) -> bool:
        """
        Returns false if there was a problem initializing the connection.
        """
        try:
            self.client: Redis = Redis(host=ip,
                                       port=port)
            self.client.ping()
            self._connected = True

            # Initialize workers
            self.candles_worker = RedisCandlesWorker(self.logfeed_program, self.client, self.env_type)
            self.health_worker = RedisHealthWorker(self.logfeed_program, self.client, self.env_type)
            self.models_worker = RedisModelsWorker(self.logfeed_program, self.client, self.env_type)
            self.strategies_worker = RedisStrategiesWorker(self.logfeed_program, self.client, self.env_type)
            self.visuals_worker = RedisVisualsWorker(self.logfeed_program, self.client, self.env_type)
            self.collection_worker = RedisCollectionWorker(self.logfeed_program, self.client, self.env_type)
            self.settings_worker = RedisSettingsWorker(self.logfeed_program, self.client, self.env_type)

        except Exception:
            self.error_main(f'Could not initialize connection to Redis database in thread #{self._pid}:')
            self.warn_main(traceback.format_exc())
            return False
        return True

    def get_prefix(self) -> str:
        """
        Returns the string which identifies the info's data environment.
        All data stored in redis must be prefixed in order to distinguish it from other environment's data.
        """
        return self.env_type.value + '_'

    def clear_db(self) -> None:
        """
        Deletes all data stored in the environment.
        """
        self.client.delete(self.get_prefix() + '*')

    """
    Trade and strategy run history storage...
    """

    def get_symbols_traded(self) -> List[str]:
        return self.strategies_worker.get_symbols_traded()

    def get_trade_history(self,
                          symbols: Optional[List[str]] = None,
                          paper: bool = False,
                          limit: int = 999) -> List[RoundTripTrade]:
        return self.strategies_worker.get_trade_history(symbols, paper, limit)

    def record_trade(self,
                     trade: RoundTripTrade,
                     endpoint: BrokerEndpoint = BrokerEndpoint.PAPER) -> None:
        return self.strategies_worker.record_trade(trade, endpoint)

    def clear_trade_history(self) -> None:
        return self.strategies_worker.clear_trade_history()

    def get_live_run_history(self,
                             strategies: List[str],
                             paper: bool = False,
                             limit: int = 999,
                             symbols: Optional[List[str]] = None) -> List[StrategyRun]:
        return self.strategies_worker.get_live_run_history(strategies, paper, limit, symbols)

    def record_live_run(self,
                        strategy_id: str,
                        run: StrategyRun,
                        endpoint: BrokerEndpoint = BrokerEndpoint.PAPER) -> None:
        return self.strategies_worker.record_live_run(strategy_id, run, endpoint)

    def remove_live_run(self,
                        strategy_id: str,
                        execution: StrategyRun) -> None:
        return self.strategies_worker.remove_live_run(strategy_id, execution)

    def get_virtual_run_history(self,
                                strategies: List[str],
                                limit: int = 999,
                                symbols: Optional[List[str]] = None) -> List[StrategyRun]:
        return self.strategies_worker.get_virtual_run_history(strategies, limit, symbols)

    def record_virtual_run(self,
                           strategy_id: str,
                           run: StrategyRun) -> None:
        return self.strategies_worker.record_live_run(strategy_id, run)

    def remove_virtual_run(self,
                           strategy_id: str,
                           run: StrategyRun) -> None:
        return self.strategies_worker.remove_virtual_run(strategy_id, run)

    def clear_run_history(self,
                          strategy_ids: List[str]) -> None:
        return self.strategies_worker.clear_run_history(strategy_ids)

    def get_simulation_output(self) -> Optional[Dict]:
        return self.strategies_worker.get_simulation_output()

    def save_simulation_output(self,
                               sim_output: Dict) -> None:
        return self.strategies_worker.save_simulation_output(sim_output)

    def clear_simulation_output(self) -> None:
        return self.strategies_worker.clear_simulation_output()

    """
    Strategy optimization storage...
    """

    def get_optimization_time(self,
                              symbol: str,
                              strategy_id: str) -> datetime:
        return self.strategies_worker.get_optimization_time(symbol, strategy_id)

    def set_optimization_time(self,
                              symbol: str,
                              strategy_id: str,
                              optimization_time: datetime) -> None:
        return self.strategies_worker.set_optimization_time(symbol, strategy_id, optimization_time)

    """
    Analysis model data storage...
    """

    def get_analysis_rolling_sum(self,
                                 symbol: str,
                                 model_type: AnalysisModelType) -> float:
        return self.models_worker.get_analysis_rolling_sum(symbol, model_type)

    def get_analysis_raw_output(self,
                                symbol: str,
                                model_type: AnalysisModelType) -> str:
        return self.models_worker.get_analysis_raw_output(symbol, model_type)

    def save_analysis_result(self,
                             symbol: str,
                             model_type: AnalysisModelType,
                             encoded_result: str) -> None:
        return self.models_worker.save_analysis_result(symbol, model_type, encoded_result)

    def get_analysis_date(self,
                          symbol: str,
                          model_type: AnalysisModelType) -> date:
        return self.models_worker.get_analysis_date(symbol, model_type)

    def get_analysis_start_date(self,
                                symbol: str,
                                model_type: AnalysisModelType,
                                today: date) -> date:
        return self.models_worker.get_analysis_start_date(symbol, model_type, today)

    def save_analysis_date(self,
                           symbol: str,
                           model_type: AnalysisModelType,
                           day_date: date) -> None:
        return self.models_worker.save_analysis_date(symbol, model_type, day_date)

    def save_analysis_start_date(self,
                                 symbol: str,
                                 model_type: AnalysisModelType,
                                 day_date: date) -> None:
        return self.models_worker.save_analysis_start_date(symbol, model_type, day_date)

    def get_analysis_snapshot_raw_output(self,
                                         symbol: str,
                                         model_type: AnalysisModelType) -> str:
        return self.models_worker.get_analysis_snapshot_raw_output(symbol, model_type)

    def save_analysis_snapshot_result(self,
                                      symbol: str,
                                      model_type: AnalysisModelType,
                                      encoded_result: str) -> None:
        return self.models_worker.save_analysis_snapshot_result(symbol, model_type, encoded_result)

    def get_analysis_snapshot_date(self,
                                   symbol: str,
                                   model_type: AnalysisModelType) -> date:
        return self.models_worker.get_analysis_snapshot_date(symbol, model_type)

    def save_analysis_snapshot_date(self,
                                    symbol: str,
                                    model_type: AnalysisModelType,
                                    day_date: date) -> None:
        return self.models_worker.save_analysis_snapshot_date(symbol, model_type, day_date)

    def remove_analysis_snapshot(self,
                                 model_type: AnalysisModelType) -> None:
        return self.models_worker.remove_analysis_snapshot(model_type)

    def remove_analysis_data(self,
                             model_type: AnalysisModelType,
                             symbols: List[str] = None) -> None:
        return self.models_worker.remove_analysis_data(model_type, symbols)

    """
    Visuals data (graphs, charts, etc.) storage...
    """

    def save_visual_data(self,
                         visual_type: VisualType,
                         visual_params: Dict[str, any],
                         data: 'AbstractVisualizationData') -> None:
        return self.visuals_worker.save_visual_data(visual_type, visual_params, data)

    def load_visual_data(self,
                         visual_type: VisualType,
                         visual_params: Dict[str, any]) -> Optional['AbstractVisualizationData']:
        return self.visuals_worker.load_visual_data(visual_type, visual_params)

    """
    Health data (health check status and debug messages) storage...
    """

    def save_health_check_result(self,
                                 check_type: HealthCheckType,
                                 check_params: Dict[str, any],
                                 result: HealthCheckResult) -> None:
        return self.health_worker.save_health_check_result(check_type, check_params, result)

    def load_health_check_result(self,
                                 check_type: HealthCheckType,
                                 check_params: Dict[str, any]) -> Optional[HealthCheckResult]:
        return self.health_worker.load_health_check_result(check_type, check_params)

    """
    Data collection cache...
    """

    def get_cached_candles(self, symbol: str, day_date: date) -> List[Candle]:
        return self.candles_worker.get_cached_candles(symbol, day_date)

    def prune_cached_candles(self, symbol: str, candles_to_keep: int = 50000) -> None:
        return self.candles_worker.prune_cached_candles(symbol, candles_to_keep)

    def store_cached_candles(self, symbol: str, candles: List[Candle]) -> None:
        return self.candles_worker.store_cached_candles(symbol, candles)

    """
    Data collection metadata...
    """

    def get_day_difficulty(self,
                           symbol: str,
                           day_date: date) -> int:
        return self.collection_worker.get_day_difficulty(symbol, day_date)

    def incr_day_difficulty(self,
                            symbol: str,
                            day_date: date) -> None:
        return self.collection_worker.incr_day_difficulty(symbol, day_date)

    def reset_day_difficulty(self,
                             symbol: str,
                             day_date: date) -> None:
        return self.collection_worker.reset_day_difficulty(symbol, day_date)

    def reset_day_difficulties(self) -> None:
        return self.collection_worker.reset_day_difficulties()

    """
    Program settings...
    """

    def get_setting(self,
                    setting_name: str) -> Optional[str]:
        return self.settings_worker.get_setting(setting_name)

    def set_setting(self,
                    setting_name: str,
                    setting_value: str) -> Optional[str]:
        return self.settings_worker.set_setting(setting_name, setting_value)
