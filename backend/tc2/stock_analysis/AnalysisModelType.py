from enum import Enum


class AnalysisModelType(Enum):
    # LongShortStrategy models
    OSCILLATION = 'OSCILLATION'
    LS_FAVOR = 'LS_FAVOR'

    # CycleStrategy models
    VOLATILITY = 'VOLATILITY'
    DIP_10 = 'DIP_10'
    DIP_45 = 'DIP_45'
    MOMENTUM = 'MOMENTUM'
    PROFITABILITY = 'PROFITABILITY'

    # Breakout1Strategy models
    BREAKOUT1_MODEL = 'BREAKOUT1_MODEL'

    # SwingStrategy models
    HIGH_96_PCT = 'HIGH_96_PCT'
    VOLUME_50 = 'VOLUME_50'
