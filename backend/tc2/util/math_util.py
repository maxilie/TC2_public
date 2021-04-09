"""Contains utility functions for performing calculations of technical indicators."""
from typing import Union, List

from tc2.data.data_structs.price_data.MinuteCandle import MinuteCandle
from tc2.data.data_structs.price_data.DailyCandle import DailyCandle
from tc2.data.data_structs.price_data.Candle import Candle


def true_range(current: Union[Candle, MinuteCandle, DailyCandle, List[Union[Candle, MinuteCandle, DailyCandle]]],
               prev: Union[Candle, MinuteCandle, DailyCandle, List[Union[Candle, MinuteCandle, DailyCandle]]]) -> float:
    """
    Returns the true range for the period, which is defined as:
        max{this_high - this_low,
            abs(this_high - prev_close),
            abs(this_low - prev_close
            }
    """
    pass


def factor_in_next_ema(next_val: float, prev_ema: float, n: int) -> float:
    """Returns the new exponential moving average given the previous period's ema and the new period's value."""
    weight = 2.0 / (1 + n)
    return (next_val * weight) + (prev_ema * (1 - weight))


def ema(vals: List[float]) -> float:
    """Returns the exponential moving average of the values."""
    result = factor_in_next_ema(next_val=vals[0], prev_ema=vals[0], n=0)
    for i in range(1, len(vals)):
        result = factor_in_next_ema(next_val=vals[i], prev_ema=result, n=i)
    return result
