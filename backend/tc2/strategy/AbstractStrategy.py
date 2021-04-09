import traceback
from datetime import datetime
from typing import Optional, Dict, List

from tc2.account import AbstractAccount
from tc2.data.data_structs.account_data.Order import Order
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.env.ExecEnv import ExecEnv
from tc2.env.Settings import Settings
from tc2.stock_analysis.AbstractModel import AbstractModel
from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.stock_analysis.ModelWeightingSystem import ModelWeightingSystem
from tc2.strategy.execution.StrategyRun import StrategyRun
from tc2.strategy.execution.StrategySymbolRun import StrategySymbolRun
from tc2.util.TimeInterval import TimeInterval
from tc2.util.model_creation import create_model
from tc2.util.optimization_util import evenly_distribute_weights


class AbstractStrategy(ExecEnv):
    """
    A strategy that can be executed live or simulated historically.
    """

    # Info about the strategy run, including the symbol, when it was bought, etc.
    run_info: StrategyRun

    # The account object providing the strategy buying and selling ability
    acct: Optional['AbstractAccount']

    # The weights placed on each analysis model used by the strategy
    scoring_system: ModelWeightingSystem

    # The analysis models used by the strategy
    models: Dict[AnalysisModelType, AbstractModel]

    # Today's results of each of the strategy's analysis models
    _model_outputs: Dict[AnalysisModelType, any]

    def __init__(self, env: ExecEnv,
                 symbols: List[str]) -> None:
        """
        :param env: the environment in which to trade
        :param symbols: the symbol(s) to trade
        """
        super().__init__(env.logfeed_program, env.logfeed_process)
        self.clone_same_thread(env)

        # Init private variables
        self._running = True
        self._model_outputs = {}
        self.run_info = StrategyRun(symbol_runs=[StrategySymbolRun(symbol, [], [], [], [], []) for symbol in symbols],
                                    strategy_start_time=self.time().now(),
                                    strategy_end_time=self.time().now(),
                                    metadata=None)

        # Init model weights.
        # self.debug_process(f'{self.get_id()} initializing analysis model weights')
        self.scoring_system = evenly_distribute_weights(pass_fail_models=self.__class__.pass_fail_models(),
                                                        min_model_weights=self.__class__.min_model_weights(),
                                                        max_model_weights=self.__class__.max_model_weights(),
                                                        logfeed_process=self.logfeed_process)

        # Create analysis models.
        # self.debug_process(f'{self.get_id()} initializing analysis models')
        self.models = {}
        for model_type in self.scoring_system.model_weights.keys():
            self.models[model_type] = create_model(env=self,
                                                   model_type=model_type)
        # self.debug_process(f'{self.get_id()} created!')

    """
    Strategy settings...
    """

    @classmethod
    def get_id(cls) -> str:
        """
        Returns the strategy's class name, which is used to id it in the database.
        """
        return cls.__name__

    def max_purchase_pct(self) -> float:
        """
        Returns the maximum percentage of the account's balance to use on the strategy.
        """
        return Settings.get_strategy_max_purchase_pct(self, self.get_id())

    def max_purchase_usd(self) -> float:
        """
        Returns the maximum percentage of the account's balance to use on the strategy.
        """
        return Settings.get_strategy_max_purchase_usd(self, self.get_id())

    @classmethod
    def times_active(cls) -> TimeInterval:
        """Returns the times of day when this strategy can be used."""
        raise NotImplementedError

    @classmethod
    def pass_fail_models(cls) -> List[AnalysisModelType]:
        """
        Returns pass/fail models, which do not have weights.
        """
        raise NotImplementedError

    @classmethod
    def min_model_weights(cls) -> Dict[AnalysisModelType, float]:
        """
        Returns the lowest weight to use for each model during optimization.
        """
        raise NotImplementedError

    @classmethod
    def max_model_weights(cls) -> Dict[AnalysisModelType, float]:
        """
        Returns the highest weight to use for each model during optimization.
        Set pass/fail model weights to 0.
        """
        raise NotImplementedError

    @classmethod
    def is_experimental(cls) -> bool:
        """
        Returns True if the strategy is not to be live-traded.
        """
        raise NotImplementedError

    def get_symbols(self) -> List[str]:
        """
        Returns the symbol being traded by the strategy.
        """
        return [symbol_run.symbol for symbol_run in self.run_info.symbol_runs]

    def set_symbols(self,
                    symbols: List[str]) -> None:
        """
        Adds to the list of symbol(s) being traded by the strategy.
        """
        self.run_info.symbol_runs = [StrategySymbolRun(symbol, [], [], [], [], []) for symbol in symbols]

    """
    Methods called at initialization...
    """

    def provide_account(self, acct: AbstractAccount) -> None:
        """
        Gives the strategy a reference to a brokerage account.
        Called by live StrategyExecutor or historical StrategySimulator.
        """
        self.acct = acct
        self.run_info.start_time = self.time().now()

    def score_symbols(self,
                      symbols: List[str] = None) -> Dict[str, float]:
        """
        Removes failing symbols and returns a map of viable symbols with their scores.
        :param symbols: defaults to all symbols
        """

        # Load all symbols from settings.
        if symbols is None:
            symbols = Settings.get_symbols(self)

        # Have every model assign every symbol a grade.
        all_symbol_grades = {}
        for symbol in symbols:
            grades_for_symbol = []
            for model_type, model_weight in self.scoring_system.model_weights.items():
                try:
                    model_output = self.models[model_type].calculate_output(symbol)
                    self._set_model_output(model_type, model_output, symbol)
                    symbol_grade = self.models[model_type].grade_symbol(symbol, model_output)
                    grades_for_symbol.append(symbol_grade)
                except Exception as e:
                    self.error_process('Error calculating model output for {} on {}: {}'
                                       .format(model_type, symbol, traceback.format_exc()))

            all_symbol_grades[symbol] = grades_for_symbol

        # Convert categorical grades to numerical scores.
        return self.scoring_system.score_symbols(all_symbol_grades)

    """
    State getter/setter methods...
    """

    def is_running(self) -> bool:
        """
        Always returns true until the strategy finishes trying to buy and sell.
        """
        return self._running

    def stop_running(self,
                     sell_price: Optional[float]) -> None:
        """
        Signals the strategy's executor or simulator that the strategy's logic has run its course.
        """
        self._running = False
        self.run_info.strategy_end_time = self.time().now()

    def mark_as_viable(self) -> None:
        """
        Remembers that the strategy & symbol became viable.
        """
        self.run_info.became_viable = True

    def mark_as_bought(self,
                       buy_time: datetime,
                       buy_price: float) -> None:
        """
        Remembers that the symbol was bought, so the strategy can run its sell logic.
        """
        self.run_info.buy_time = buy_time
        self.run_info.buy_price = buy_price

    """
    Methods called repeatedly during execution...
    """

    def on_new_info(self,
                    symbol: str,
                    moment: datetime,
                    candle: Optional[Candle] = None,
                    order: Optional[Order] = None) -> None:
        """
        Called when an order changes status or a new candle becomes available.
        This is where the strategy should cache the data, run calculations, and call its buy or sell logic.
        :param symbol: the symbol being updated
        :param moment: the datetime of this latest info - to be used in place of datetime.now()
        :param candle: the latest candlestick, or None if this is an order update
        :param order: the updated order, or None if this is a price update
        """
        raise NotImplementedError

    def buy_logic(self) -> None:
        """
        Logic to called frequently by the StrategyExecutor or StrategySimulator.
        Set self.bought = True to signal the Executor or Simulator to move on to sell_logic.
        Set self.running = False to signal the Executor or Simulator to end early.
        """
        raise NotImplementedError

    def sell_logic(self) -> None:
        """
        Logic to called frequently by the StrategyExecutor or StrategySimulator.
        Set self.running = False to signal the Executor or Simulator to stop calling.
        """
        raise NotImplementedError

    def get_model_output(self,
                         model_type: AnalysisModelType,
                         symbol: str) -> any:
        """
        Returns the output of an analysis model, if score_symbols() was called first.
        This is used, for example, when the strategy uses the target price calculated
            by one of its analysis models.
        """
        return self._model_outputs[model_type][symbol] \
            if model_type in self._model_outputs.keys() and symbol in self._model_outputs[model_type].keys() \
            else None

    """
    Private methods...
    """

    def _set_model_output(self, model_type: AnalysisModelType,
                          model_output: any,
                          symbol: str) -> None:
        """
        Allows the strategy access to the output of an analysis model calculation at execution time,
            via get_model_output(model_type).
        """
        if model_type not in self._model_outputs:
            self._model_outputs[model_type] = {}
        self._model_outputs[model_type][symbol] = model_output
