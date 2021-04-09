from enum import Enum


class HealthCheckType(Enum):
    ALPACA = 'ALPACA'
    MODEL_FEEDING = 'MODEL_FEEDING'
    DATA = 'DATA'
    DIP45 = 'DIP45'
    MONGO = 'MONGO'
    POLYGON = 'POLYGON'
    SIM_OUTPUT = 'SIM_OUTPUT'
    SIM_TIMINGS = 'SIM_TIMINGS'
