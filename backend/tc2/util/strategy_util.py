from __future__ import annotations

from typing import List

from tc2.env.ExecEnv import ExecEnv
from tc2.util.strategy_constants import DAY_STRATEGY_CLASSES, SWING_STRATEGY_CLASSES


def create_day_strategies(env: ExecEnv) -> List['AbstractStrategy']:
    """
    Creates AbstractStrategy objects for all available day-trading strategies, and assigns them env objects.
    """
    return [
        cls(env=env,
            symbols=['DUMMY']) for cls in DAY_STRATEGY_CLASSES
    ]


def create_swing_strategies(env: ExecEnv) -> List['AbstractStrategy']:
    """
    Creates AbstractStrategy objects for all available swing-trading strategies, and assigns them env objects.
    """
    return [
        cls(env=env,
            symbols=['DUMMY']) for cls in SWING_STRATEGY_CLASSES
    ]
