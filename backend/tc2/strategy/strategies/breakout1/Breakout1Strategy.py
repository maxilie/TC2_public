import math
from datetime import datetime, timedelta, time
from typing import Optional, List, Dict

from tc2.data.data_structs.account_data.Order import Order
from tc2.data.data_structs.account_data.OrderStatus import OrderStatus
from tc2.data.data_structs.account_data.OrderType import OrderType
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.env.ExecEnv import ExecEnv
from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.strategy.AbstractStrategy import AbstractStrategy
from tc2.strategy.strategies.breakout1 import breakout1_constants
from tc2.util.TimeInterval import TimeInterval
from tc2.util.date_util import TIME_FORMAT


class Breakout1Strategy(AbstractStrategy):
    """
    Breakout1Strategy looks for a breakout setup with a few other conditions.
    """

    @classmethod
    def times_active(cls) -> TimeInterval:
        return TimeInterval(logfeed=None,
                            start1=time(hour=10, minute=30),
                            end1=time(hour=15, minute=0))

    @classmethod
    def pass_fail_models(cls) -> List[AnalysisModelType]:
        return [
            AnalysisModelType.BREAKOUT1_MODEL
        ]

    @classmethod
    def min_model_weights(cls) -> Dict[AnalysisModelType, float]:
        return {
        }

    @classmethod
    def max_model_weights(cls) -> Dict[AnalysisModelType, float]:
        return {
        }

    @classmethod
    def is_experimental(cls) -> bool:
        return True

    # Store up to BREAKOUT_SETUP_MINS minutes of recent data
    recent_candles: List[Candle]
    printed_buy_start: bool
    printed_sell_start: bool
    times_lowered: int
    sell_target: Optional[float]

    def __init__(self,
                 env: ExecEnv,
                 symbols: List[str]) -> None:
        super().__init__(env=env,
                         symbols=symbols)

        # Private variables
        self.recent_candles = []
        self.printed_buy_start = False
        self.printed_sell_start = False
        self.sell_target = None

    def on_new_info(self, symbol: str, moment: datetime, candle: Optional[Candle] = None,
                    order: Optional[Order] = None) -> None:
        # Ignore old updates and updates on other symbols
        if symbol != self.get_symbols()[0]:
            return

        # Absorb the new data into the strategy's short-term (last 5 minutes) memory
        if candle is not None:
            self.merge_candle(candle)

        # Check to mark the symbol as bought
        if self.run_info.buy_time is None and order is not None and order.type == OrderType.LIMIT_BUY \
                and order.status == OrderStatus.FILLED:
            self.run_info.buy_time = moment
            self.buy_price = order.get_price()

        # Record the order sell price when the symbol sells
        if order is not None and self.symbol_was_sold():
            self.sell_target = order.get_price()

        # TODO Remove this debug output
        if candle is not None:
            self.info_process(
                'New price: ${}  at {}'.format("%.2f" % candle.close, candle.moment.strftime(TIME_FORMAT)))

        # Run the strategy's buy or sell logic
        if self.run_info.buy_time is None:
            self.buy_logic()
        else:
            self.sell_logic()

    def buy_logic(self) -> None:
        if self.insufficient_funds():
            self.acct.cancel_open_orders(self.get_symbols())
            self.info_process('Breakout1Strategy ending buy logic. Insufficient funds')
            self.stop_running(sell_price=None)
            return

        # Place the buy order
        if not self.printed_buy_start:
            if len(self.recent_candles) == 0:
                self.info_process('Breakout1Strategy waiting for price data')
                return
            latest_price = self.recent_candles[-1].low
            self.buy_price = latest_price + max(0.01, latest_price * (breakout1_constants.RAISE_BUY_PERCENT / 100))
            self.qty = self.get_qty_at_price(self.buy_price)
            if self.acct.place_limit_buy(self.get_symbols()[0], self.buy_price, self.qty):
                self.info_process(
                    'Starting Breakout1Strategy buy logic on ' + str(
                        self.qty) + ' ' + self.get_symbols()[0] + ' for $' + str(
                        self.buy_price))
                self.printed_buy_start = True
            else:
                self.warn_process('Breakout1Strategy couldn\'t place buy order')
            return

        # Wait for the price to dip and trigger our buy order

        if self.climbed_too_much():
            self.info_process('Breakout1Strategy ending buy logic after price climbed too high')
            self.stop_running(sell_price=None)
            return

        if self.waited_too_long_for_buy():
            self.info_process('Breakout1Strategy ending buy logic after waiting too long for a buy order to go through')
            self.stop_running(sell_price=None)
            return

    def sell_logic(self) -> None:
        # Don't sell until the brokerage confirms our new positions
        if self.not_bought_yet():
            self.warn_process("Breakout1Strategy can't sell while new positions not detected")
            return

        # Get cached latest price
        current_price = self.recent_candles[-1].close

        # Place first sell order and initialize variables
        if not self.printed_sell_start:
            # TODO Set stop_price to the support minus epsilon
            self.stop_price = self.buy_price * (1 - (breakout1_constants.MAX_STOP_PCT / 100))
            self.sell_target = self.stop_price
            self.info_process(
                'Breakout1Strategy initial stop order: {0} {1} for ${2}'.format(
                    self.qty, self.get_symbols()[0], self.stop_price))
            self.printed_sell_start = True
            self.acct.place_stop_order(self.get_symbols()[0], self.sell_target, self.qty)
            return

        # End when the symbol gets sold
        if self.symbol_was_sold():
            self.info_process(
                'Breakout1Strategy sold {0} {1} for {2}% profit after {3} seconds'.format(
                    self.qty,
                    self.get_symbols()[0],
                    "%.2f" % (100 * (self.sell_target - self.buy_price) / self.buy_price),
                    "%.2f" % (self.time().now() - self.run_info.buy_time).total_seconds()
                ))
            self.stop_running(sell_price=self.sell_target)
            return

        # Dump the symbol when the market is nearing closing time
        if self.market_closes_soon():
            self.sell_target = current_price * (1 + (0.05 / 100))
            if self.too_close_to_last_offer():
                return
            self.acct.place_limit_sell(self.get_symbols()[0], self.sell_target, self.qty)
            self.info_process('Breakout1Strategy placing non-greedy offer since markets close soon: ${0}'
                              .format("%.2f" % self.sell_target))
            return

        # A) [y < -0.3%] Look ahead to cut losses (i.e. place a stop order) when the price dips low
        if current_price < self.buy_price * (1 - (0.3 / 100)):
            self.sell_target = self.stop_price
            if self.too_close_to_last_offer():
                return
            self.acct.place_stop_order(self.get_symbols()[0], self.sell_target, self.qty)
            self.info_process(
                'Breakout1Strategy placing stop order at ${0}'.format("%.2f" % self.sell_target))
            return

        # TODO If it's been a long time since starting to sell, set a modest offer
        # Determine the lowest offer we could reasonably make
        safety_sell_point = max(self.buy_price, current_price) * (1 + breakout1_constants.MIN_SALE_PROFIT / 100)

        # TODO Place limit sell order just below the resistance line

    def insufficient_funds(self) -> bool:
        return self.acct.withdrawable_balance < breakout1_constants.MIN_PURCHASE

    def not_bought_yet(self) -> bool:
        return self.run_info.buy_time is None and self.acct.positions is None

    def climbed_too_much(self) -> bool:
        return self.recent_candles[-1].close >= self.buy_price * (
                1.0 + (breakout1_constants.MAX_PCT_INCREASE_BEFORE_BUY / 100.0))

    def waited_too_long_for_buy(self) -> bool:
        return self.time().now() >= self.run_info.start_time + timedelta(seconds=breakout1_constants.MAX_BUY_TIME)

    def symbol_was_sold(self) -> bool:
        return self.run_info.buy_time is not None and self.sell_target is not None and self.acct.positions is None

    def market_closes_soon(self) -> bool:
        return self.time().get_secs_to_close() < 60 * 45

    def get_offer_price(self) -> Optional[float]:
        return None if self.acct.open_orders is None else self.acct.open_orders.price

    def too_close_to_last_offer(self) -> bool:
        last_offer = self.get_offer_price()
        if last_offer is not None and abs(last_offer - self.sell_target) < 0.06 / 100:
            self.sell_target = last_offer
            return True
        return False

    def merge_candle(self, candle: Candle) -> None:
        """Stores the new candle and forgets another if necessary."""
        self.recent_candles.append(candle)
        if len(self.recent_candles) <= 60 * breakout1_constants.BREAKOUT_SETUP_MINS:
            return
        oldest_candle = None
        for c in self.recent_candles:
            if oldest_candle is None or c.moment < oldest_candle.moment:
                oldest_candle = c
        self.recent_candles.remove(oldest_candle)

    def get_qty_at_price(self, price: float) -> int:
        """Return the max shares that can be bought at the given price per share."""
        shares = int(math.floor((self.max_purchase_pct() * self.acct.withdrawable_balance) / price))
        return min(shares,
                   int(math.floor(self.max_purchase_usd() / price)))
