from typing import List, Optional

from tc2.util.data_constants import DATA_SPLITTERS


class ProfitabilitySimulationResults:
    """
    Contains the output of a ProfitabilityModel, which is a statistical analysis of historical StopSellSimulations.
    """
    target_avg_pct_profits: List[float]
    target_med_pct_profits: List[float]

    def __init__(self, target_avg_pct_profits, target_med_pct_profits) -> None:
        self.target_avg_pct_profits = target_avg_pct_profits
        self.target_med_pct_profits = target_med_pct_profits

    def __str__(self) -> str:
        """Encodes a ProfitabilityCheckResult into a string."""
        return DATA_SPLITTERS['level_1'].join([
            DATA_SPLITTERS['level_2'].join([str(profit) for profit in self.target_avg_pct_profits]),
            DATA_SPLITTERS['level_2'].join([str(profit) for profit in self.target_med_pct_profits])
        ])

    @classmethod
    def from_str(cls, data_str: str) -> Optional['ProfitabilitySimulationResults']:
        if data_str is None or len(data_str) == 0:
            return None
        components = data_str.split(DATA_SPLITTERS['level_1'])
        target_avg_pct_profits = [float(profit) for profit in components[0].split(DATA_SPLITTERS['level_2'])]
        target_med_pct_profits = [float(profit) for profit in components[1].split(DATA_SPLITTERS['level_2'])]
        return ProfitabilitySimulationResults(target_avg_pct_profits, target_med_pct_profits)
