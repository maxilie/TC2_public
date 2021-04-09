from typing import List, Optional

import numpy as np
from scipy.signal import savgol_filter as smooth

from tc2.stock_analysis.model_output.PriceLine import PriceLine
from tc2.data.data_structs.price_data.Candle import Candle


class TrendLineFinder:
    """
    Finds support and resistance lines.
    """

    # The number of candles (seconds) to use in the sliding window;
    # This sliding window detects minima/maxima when sign([0,0.5]) != sign([0.5,1]);
    # Must be an even number
    n: int = 70

    @classmethod
    def find_support_line(cls,
                          candles: List[Candle]) -> Optional[PriceLine]:
        """
        Returns a support line, if one can be found.
        """

        if len(candles) < cls.n * 3:
            raise ValueError(f'Cannot find support line with fewer than {cls.n * 3} candles')

        prices = np.array([(candle.low + candle.open) / 2.0 for candle in candles])

        # Smoothen the curve
        prices_smooth = smooth(prices, (cls.n + 1), 3)

        # Take the derivative as the difference of consecutive prices
        prices_dydx = np.zeros(len(candles))
        prices_dydx[1:] = np.subtract(prices_smooth[1:], prices_smooth[:-1])

        lowest_moments = [candles[0].moment, candles[3].moment]
        lowest_prices = [(candles[0].low + candles[0].open) / 2.0, (candles[0].low + candles[0].open) / 2.0]

        for i in range(len(candles) - cls.n):
            midpoint: int = int(cls.n / 2)
            arr_sl = prices_dydx[i:(i + cls.n)]
            first_half = arr_sl[:midpoint]
            last_half = arr_sl[midpoint:]

            s_1 = np.sum(first_half < 0)
            s_2 = np.sum(last_half > 0)

            candle = candles[i + (midpoint - 1)]
            price = (candle.low + candle.open) / 2.0

            # Detect a local minimum
            if s_1 == cls.n / 2 == s_2:
                if price < min(lowest_prices):
                    # Insert the lowest value first, drop the third (and largest) value
                    lowest_moments.insert(0, candle.moment)
                    lowest_moments = lowest_moments[:2]
                    lowest_prices.insert(0, price)
                    lowest_prices = lowest_prices[:2]

        return PriceLine(point_1_moment=lowest_moments[0],
                         point_1_price=lowest_prices[0],
                         point_2_moment=lowest_moments[1],
                         point_2_price=lowest_prices[1],
                         first_moment=candles[0].moment,
                         last_moment=candles[-1].moment)

    @classmethod
    def find_resistance_line(cls,
                             candles: List[Candle]) -> Optional[PriceLine]:
        """
        Returns a resistance line, if one can be found.
        """

        if len(candles) < cls.n * 3:
            raise ValueError(f'Cannot find resistance line with fewer than {cls.n * 3} candles')

        prices = np.array([(candle.high + candle.open) / 2.0 for candle in candles])

        # Smoothen the curve
        prices_smooth = smooth(prices, (cls.n + 1), 3)

        # Take the derivative as the difference of consecutive prices
        prices_dydx = np.zeros(len(candles))
        prices_dydx[1:] = np.subtract(prices_smooth[1:], prices_smooth[:-1])

        highest_moments = [candles[0].moment, candles[3].moment]
        highest_prices = [(candles[0].high + candles[0].open) / 2.0, (candles[0].high + candles[0].open) / 2.0]

        for i in range(len(candles) - cls.n):
            midpoint: int = int(cls.n / 2)
            arr_sl = prices_dydx[i:(i + cls.n)]
            first_half = arr_sl[:midpoint]
            last_half = arr_sl[midpoint:]

            r_1 = np.sum(first_half > 0)
            r_2 = np.sum(last_half < 0)

            candle = candles[i + (midpoint - 1)]
            price = (candle.high + candle.open) / 2.0

            # Detect a local maximum
            if r_1 == cls.n / 2 == r_2:
                if price < min(highest_prices):
                    # Insert the lowest value first, drop the third (and smallest) value
                    highest_moments.insert(0, candle.moment)
                    highest_moments = highest_moments[:2]
                    highest_prices.insert(0, price)
                    highest_prices = highest_prices[:2]

        return PriceLine(point_1_moment=highest_moments[0],
                         point_1_price=highest_prices[0],
                         point_2_moment=highest_moments[1],
                         point_2_price=highest_prices[1],
                         first_moment=candles[0].moment,
                         last_moment=candles[-1].moment)
