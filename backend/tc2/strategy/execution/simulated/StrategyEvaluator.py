from tc2.env.ExecEnv import ExecEnv
from tc2.strategy.AbstractStrategy import AbstractStrategy
from tc2.strategy.execution.simulated.StrategyEvaluation import StrategyEvaluation
from tc2.strategy.execution.simulated.StrategySimulator import StrategySimulator


class StrategyEvaluator(ExecEnv):
    """
    Runs trade simulations during a historical day.
    """
    strategy: AbstractStrategy

    def __init__(self, strategy: AbstractStrategy) -> None:
        super().__init__(strategy.logfeed_program, strategy.logfeed_process)
        self.clone_same_thread(strategy)

        self.strategy = strategy

    def evaluate(self) -> StrategyEvaluation:
        executions = []
        simulator = StrategySimulator(self.strategy, self)
        self.info_process('DEBUG: StrategyEvaluator beginning simulation')
        execution = simulator.run()
        executions.append(execution)

        return StrategyEvaluation(executions)
