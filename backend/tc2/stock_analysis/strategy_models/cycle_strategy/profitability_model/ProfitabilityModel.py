from datetime import timedelta
from statistics import mean, median
from typing import Optional, List, Dict

from tc2.stock_analysis.AbstractSpotModel import AbstractSpotModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade, SymbolGradeValue
from tc2.stock_analysis.strategy_models.cycle_strategy.profitability_model.ProfitabilitySimulationResults import \
    ProfitabilitySimulationResults
from tc2.stock_analysis.strategy_models.cycle_strategy.profitability_model.StopSellSimulation import StopSellSimulationResult, \
    StopSellSimulation


class ProfitabilityModel(AbstractSpotModel):
    OUTPUT_TYPE = Optional[ProfitabilitySimulationResults]
    MIN_DAYS = 100
    PCT_PROFIT_TARGETS = [0.25, 0.31, 0.34, 0.36, 0.39, 0.42, 0.45, 0.49, 0.52, 0.57, 0.61]
    STOP_PCT = 0.85

    def calculate_output(self, symbol: str) -> OUTPUT_TYPE:

        # Get all market data from the past 300 calendar days
        dates = self.mongo().get_dates_on_file(symbol, self.time().now() - timedelta(days=301),
                                               self.time().now() - timedelta(days=1))

        # Make sure the model_type runs on a sufficiently large sample size
        if len(dates) < ProfitabilityModel.MIN_DAYS:
            return None

        # Init a weighted list of profit realized using each profit target in simulation, favoring recent days
        target_realized_pct_profits: Dict[float, List[float]] = {}
        for profit_target in ProfitabilityModel.PCT_PROFIT_TARGETS:
            target_realized_pct_profits[profit_target] = []
        time_weight = 0.5
        time_weight_increment = 1 / len(dates)

        # Simulate targeting each profit target
        for day in dates:
            day_data = self.mongo().load_symbol_day(symbol, day)
            simulation = StopSellSimulation(symbol, day_data, self.time())
            for profit_target in ProfitabilityModel.PCT_PROFIT_TARGETS:
                simulation.run(ProfitabilityModel.STOP_PCT, profit_target)
                if simulation.result is StopSellSimulationResult.ERROR \
                        or simulation.result is StopSellSimulationResult.LOSS:
                    # We lost the entire stop-order amount if the price dipped enough to trigger it
                    target_realized_pct_profits[profit_target].append(ProfitabilityModel.STOP_PCT * time_weight)
                elif simulation.result is StopSellSimulationResult.NEVER_SOLD:
                    # We lost/gained some amount between stop price and target price if neither was reached
                    target_realized_pct_profits[profit_target].append(-0.1 * time_weight)
                elif simulation.result is StopSellSimulationResult.PROFIT:
                    # We gained the profit target amount if it was reached
                    target_realized_pct_profits[profit_target].append(profit_target * time_weight)
            time_weight += time_weight_increment

        # Use list to calculate average and median realized profit for each target
        target_avg_pct_profits = []
        target_med_pct_profits = []
        for profit_target in ProfitabilityModel.PCT_PROFIT_TARGETS:
            target_avg_pct_profits.append(mean(target_realized_pct_profits[profit_target]))
            target_med_pct_profits.append(median(target_realized_pct_profits[profit_target]))

        return ProfitabilitySimulationResults(target_avg_pct_profits, target_med_pct_profits)

    def grade_symbol(self, symbol: str, output: OUTPUT_TYPE) -> SymbolGrade:
        """Returns a grade based on % of profit targets that yield profit in simulation."""

        # Fail the symbol if it has no output
        if output is None:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)

        # Fail the symbol if the median of median daily profits is negligible
        if median(output.target_med_pct_profits) < 0.05:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)

        # Fail the symbol if the median of average daily profits is negligible
        if median(output.target_avg_pct_profits) < 0.05:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)

        # Assign the symbol a higher grade for higher profits
        profits = median(output.target_avg_pct_profits)
        if profits < 0.07:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.RISKY)
        elif profits < 0.09:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.UNPROMISING)
        elif profits < 0.12:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.SATISFACTORY)
        elif profits < 0.15:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.GOOD)
        elif profits < 0.2:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.GREAT)
        else:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.EXCELLENT)
