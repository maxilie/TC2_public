from datetime import timedelta, datetime, time
from enum import Enum

from tc2.env import TimeEnv
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.log.LogFeed import LogLevel


class StopSellSimulationResult(Enum):
    """An enum of all possible simulation outcomes."""
    ERROR = 1
    PROFIT = 2
    LOSS = 3
    NEVER_SOLD = 4


class StopSellSimulation:
    """Simulates buying a symbol at 10:45AM and trying to sell for profit or cut losses."""

    result: StopSellSimulationResult

    def __init__(self, symbol: str, day_data: SymbolDay, time_env: TimeEnv) -> None:
        # Private variables
        self.symbol: str = symbol
        self.day_data: SymbolDay = day_data
        self.frame: TimeEnv = time_env

        # Public variables
        self.result = StopSellSimulationResult.NEVER_SOLD

    def run(self, stop_pct: float, sell_target_pct: float) -> None:
        # Get price data at 10:30AM
        earliest_buy = datetime.combine(self.frame.now(), time(hour=10, minute=30))
        latest_buy = datetime.combine(self.frame.now(), time(hour=11, minute=0))
        sim_time = earliest_buy + timedelta(seconds=(earliest_buy - latest_buy).total_seconds() / 2)
        first_candle = self.day_data.get_candle_at_sec(sim_time)

        # Validate initial data, init variables
        if first_candle is None or first_candle.open < 1:
            self.frame.log(LogLevel.WARNING, 'CycleBuySimulation missing opening candle!')
            self.result = StopSellSimulationResult.ERROR
            return
        buy_price = first_candle.open
        first_candle_index = self.day_data.candles.index(first_candle, 0, -1)
        floor_price = buy_price - (buy_price * stop_pct / 100)
        sell_price = buy_price + (buy_price * sell_target_pct / 100)
        consec_bad_secs = 0
        total_bad_secs = 0

        # Simulate limit-buy and limit-sell orders
        for candle in self.day_data.candles[first_candle_index:-1]:
            # Validate next second's data
            if candle is None or candle.open < 1 or candle.low < 1 or candle.high < 0:
                total_bad_secs += 1
                consec_bad_secs += 1
                if consec_bad_secs == 5:
                    # Do not use this day if it's missing 5+ consecutive seconds of data
                    self.result = StopSellSimulationResult.ERROR
                    return
                if total_bad_secs == 120:
                    # Do not use this day if it's missing 120+ seconds of data
                    self.result = StopSellSimulationResult.ERROR
                    return
            else:
                consec_bad_secs = 0

            # Check to sell for a loss
            if candle.low <= floor_price:
                self.result = StopSellSimulationResult.LOSS
                return

            # Check to sell for a profit
            if candle.open >= sell_price:
                self.result = StopSellSimulationResult.PROFIT
                return
