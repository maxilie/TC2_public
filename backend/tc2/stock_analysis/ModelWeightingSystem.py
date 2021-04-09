from enum import Enum
from typing import Dict, List

from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.log.LogFeed import LogFeed, LogLevel
from tc2.util.data_constants import DATA_SPLITTERS


class SymbolGradeValue(Enum):
    """Represents a grade given to a symbol by an analysis model."""

    # A FAIL automatically disqualifies a symbol from being bought
    FAIL = -99999
    # A PASS does not hurt or harm a symbol's rating
    PASS = -1
    # The following grades rate a symbol from 1 to 10
    EXCELLENT = 10
    GREAT = 8
    GOOD = 6.5
    SATISFACTORY = 5
    UNPROMISING = 3
    RISKY = 1


class SymbolGrade:
    """Contains a symbol, a model, and the model's grade for the symbol."""

    symbol: str
    model_type: AnalysisModelType
    value: SymbolGradeValue

    def __init__(self, symbol: str, model_type: AnalysisModelType, value: SymbolGradeValue):
        self.symbol = symbol
        self.model_type = model_type
        self.value = value


class ModelWeightingSystem:
    """A system used by a strategy to assign weights to different models."""

    # A map containing the weight of each model
    model_weights: Dict[AnalysisModelType, float]

    def __init__(self, model_weights: Dict[AnalysisModelType, float], logfeed_process: LogFeed):
        self.model_weights = model_weights

        # If the scoring system has no models, leave it blank
        if len(model_weights.keys()) == 0:
            return

        weights_total = sum(model_weights.values())
        if abs(weights_total - 1) > 0.01 and sum(self.model_weights.values()) > 0.0001:
            logfeed_process.log(LogLevel.WARNING, 'ModelWeightingSystem weights do not sum up to 1!')

    def score_symbols(self, symbol_grades: Dict[str, List['SymbolGrade']]) -> Dict[str, float]:
        """
        Removes failing symbols and returns a map of each symbol to its score (1 to 10).
        """

        # Init map to be filled with symbol scores
        symbol_scores = {}

        # Score each symbol.
        for symbol in symbol_grades.keys():
            # Init list of symbol's scores.
            grade_scores = []
            symbol_fails = False

            # Convert each grade to a score.
            for grade in symbol_grades[symbol]:
                # Do not factor grades of PASS into the score calculation.
                if grade.value == SymbolGradeValue.PASS:
                    continue

                # Mark symbol as failed if it has a single grade of FAIL.
                if grade.value == SymbolGradeValue.FAIL:
                    symbol_fails = True
                    break

                # Weight the grade according the significance of the model.
                grade_scores.append(grade.value.value * self.model_weights[grade.model_type])

            # Record symbol score if it hasn't failed any checks.
            if not symbol_fails:
                # Calculate symbol's final score to be the average of each model's weighted score.
                symbol_scores[symbol] = None if len(grade_scores) == 0 else sum(grade_scores) / len(grade_scores)

        # Sort symbol scores.
        return symbol_scores

    def __str__(self) -> str:
        data_strs = []
        for model_type, model_weight in self.model_weights:
            data_strs.append(model_type.value + ':' + str(model_weight))
        return DATA_SPLITTERS['level_1'].join(data_strs)

    @classmethod
    def from_str(cls, data_str: str, logfeed_process: LogFeed) -> 'ModelWeightingSystem':
        key_pairs = data_str.split(DATA_SPLITTERS['level_1'])
        model_weights = {}
        for data_str in key_pairs:
            comps = data_str.split(':')
            model_type_str = comps[0]
            model_weight_str = comps[1]
            model_weights[AnalysisModelType[model_type_str]] = float(model_weight_str)
        return ModelWeightingSystem(model_weights, logfeed_process)
