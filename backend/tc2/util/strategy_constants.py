from tc2.strategy.strategies.ReCycleStrategy import ReCycleStrategy
from tc2.strategy.strategies.breakout1.Breakout1Strategy import Breakout1Strategy
from tc2.strategy.strategies.cycle.CycleStrategy import CycleStrategy
from tc2.strategy.strategies.long_short.LongShortStrategy import LongShortStrategy
from tc2.strategy.strategies.swing1.SwingStrategy import SwingStrategy

DAY_STRATEGY_CLASSES = [CycleStrategy,
                        ReCycleStrategy,
                        Breakout1Strategy,
                        LongShortStrategy]

DAY_STRATEGY_IDS = [strategy_cls.get_id() for strategy_cls in DAY_STRATEGY_CLASSES]

SWING_STRATEGY_CLASSES = [SwingStrategy]

SWING_STRATEGY_IDS = [strategy_cls.get_id() for strategy_cls in SWING_STRATEGY_CLASSES]
