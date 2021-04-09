from __future__ import annotations

from typing import List

from tc2.stock_analysis.AbstractModel import AbstractModel
from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.stock_analysis.strategy_models.breakout1_strategy.Breakout1Model import Breakout1Model
from tc2.stock_analysis.strategy_models.cycle_strategy.Dip10Model import Dip10Model
from tc2.stock_analysis.strategy_models.cycle_strategy.Dip45Model import Dip45Model
from tc2.stock_analysis.strategy_models.cycle_strategy.MomentumModel import MomentumModel
from tc2.stock_analysis.strategy_models.cycle_strategy.VolatilityModel import VolatilityModel
from tc2.stock_analysis.strategy_models.cycle_strategy.profitability_model.ProfitabilityModel import ProfitabilityModel
from tc2.stock_analysis.strategy_models.long_short_strategy.LSFavorModel import LSFavorModel
from tc2.stock_analysis.strategy_models.long_short_strategy.OscillationModel import OscillationModel
from tc2.stock_analysis.strategy_models.swing_strategy.High96PctModel import High96PctModel
from tc2.stock_analysis.strategy_models.swing_strategy.Volume50Model import Volume50Model
from tc2.env.ExecEnv import ExecEnv

MODEL_CLASSES = {
    # LongShortStrategy models
    AnalysisModelType.OSCILLATION    : OscillationModel,
    AnalysisModelType.LS_FAVOR       : LSFavorModel,

    # CycleStrategy models
    AnalysisModelType.VOLATILITY     : VolatilityModel,
    AnalysisModelType.MOMENTUM       : MomentumModel,
    AnalysisModelType.PROFITABILITY  : ProfitabilityModel,
    AnalysisModelType.DIP_10         : Dip10Model,
    AnalysisModelType.DIP_45         : Dip45Model,

    # Breakout1Strategy models
    AnalysisModelType.BREAKOUT1_MODEL: Breakout1Model,

    # SwingStrategy models
    AnalysisModelType.HIGH_96_PCT: High96PctModel,
    AnalysisModelType.VOLUME_50: Volume50Model
}


def create_models(env: ExecEnv) -> List[AbstractModel]:
    """Returns a list of models living within the given ExecEnv."""
    for model_type in AnalysisModelType:
        if model_type not in MODEL_CLASSES:
            env.warn_process(f'MISSING MODEL TYPE -> MODEL CLASS MAPPING FOR {model_type.name}')
    models = []
    for model_type, cls in MODEL_CLASSES.items():
        models.append(cls(env=env,
                          model_type=model_type))

    return models


def create_model(env: ExecEnv,
                 model_type: AnalysisModelType) -> AbstractModel:
    """
    Returns an instance of the model corresponding to AnalysisModelType.
    """
    cls = MODEL_CLASSES[model_type]

    return cls(env=env,
               model_type=model_type)
