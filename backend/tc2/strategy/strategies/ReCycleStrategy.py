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
from tc2.strategy.strategies.cycle import cycle_constants
from tc2.util.TimeInterval import TimeInterval
from tc2.util.date_util import TIME_FORMAT


class ReCycleStrategy(AbstractStrategy):
    """
    ReCycleStrategy is the same as CycleStrategy except it has fewer filters and it runs during more market hours.
    """

    @classmethod
    def times_active(cls) -> TimeInterval:
        return TimeInterval(logfeed=None,
                            start1=time(hour=11, minute=5),
                            end1=time(hour=15, minute=0))

    @classmethod
    def pass_fail_models(cls) -> List[AnalysisModelType]:
        return [
            AnalysisModelType.VOLATILITY,
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

    # Stores up to 5 minutes of the latest data (i.e. up to 350 candles)
    candles_5: List[Candle]
    printed_buy_start: bool
    printed_sell_start: bool
    next_adjustment: datetime
    times_lowered: int
    sell_target: Optional[float]

    def __init__(self,
                 env: ExecEnv,
                 symbols: List[str]) -> None:
        super().__init__(env=env,
                         symbols=symbols)

        # Private variables
        self.candles_5 = []
        self.printed_buy_start = False
        self.printed_sell_start = False
        self.next_adjustment = self.time().now()
        self.times_lowered = 0
        self.sell_target = None

    def on_new_info(self, symbol: str, moment: datetime, candle: Optional[Candle] = None,
                    order: Optional[Order] = None) -> None:
        # Ignore updates on other symbols
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
        """self.info_process('ReCycleStrategy running buy logic at {0}:{1}:{2}'
                          .format(self.live_time_env.now().hour,
                                  self.live_time_env.now().minute,
                                  self.live_time_env.now().second))"""
        if self.insufficient_funds():
            self.acct.cancel_open_orders(self.get_symbols())
            self.info_process('ReCycleStrategy ending buy logic. Insufficient funds')
            self.stop_running(sell_price=None)
            return

        # Place the first order
        if not self.printed_buy_start:
            if len(self.candles_5) == 0:
                self.info_process('ReCycleStrategy waiting for price data')
                return
            latest_price = self.candles_5[-1].low
            self.buy_price = latest_price - max(0.01, latest_price * (cycle_constants.LOWER_BUY_PCT / 100))
            self.qty = self.get_qty_at_price(self.buy_price)
            if self.acct.place_limit_buy(self.get_symbols()[0], self.buy_price, self.qty):
                self.info_process(
                    'Starting ReCycleStrategy buy logic on ' + str(self.qty) + ' ' + self.get_symbols()[
                        0] + ' for $' + str(
                        self.buy_price))
                self.printed_buy_start = True
            else:
                self.warn_process('ReCycleStrategy couldn\'t place buy order')
            return

        # Wait for the price to dip and trigger our buy order

        if self.climbed_too_much():
            self.info_process('ReCycleStrategy ending buy logic after price climbed too high')
            self.stop_running(sell_price=None)
            return

        if self.waited_too_long_for_dip():
            self.info_process('ReCycleStrategy ending buy logic after waiting too long for a price dip')
            self.stop_running(sell_price=None)
            return

    def sell_logic(self) -> None:
        # self.info_process('ReCycleStrategy running sell logic at {0}'.format(self.live_time_env.now()))
        # Don't sell until the brokerage confirms our new positions
        if self.not_bought_yet():
            self.warn_process("ReCycleStrategy can't sell while new positions not detected")
            return

        # Get cached latest price
        current_price = self.candles_5[-1].close

        # Determine the lowest offer we could reasonably make
        safety_sell_point = max(self.buy_price, current_price) * (1 + cycle_constants.MIN_SALE_PROFIT / 100)

        # Determine the greediest offer we could reasonably make
        greedy_sell_point = max(self.buy_price, current_price) * (1 + (cycle_constants.MAX_SALE_PROFIT / 100))

        # Place first sell order and initialize variables
        if not self.printed_sell_start:
            self.stop_price = self.buy_price * (1 - (cycle_constants.MAX_STOP_PCT / 100))
            self.sell_target = self.stop_price
            self.info_process(
                'ReCycleStrategy initial stop order: {0} {1} for ${2}'.format(
                    self.qty, self.get_symbols()[0], self.stop_price))
            self.printed_sell_start = True
            self.acct.place_stop_order(self.get_symbols()[0], self.sell_target, self.qty)
            self.next_adjustment = self.time().now() + timedelta(seconds=3)
            return

        # End when the symbol gets sold
        if self.symbol_was_sold():
            self.info_process(
                'ReCycleStrategy sold {0} {1} for {2}% profit after {3} seconds'.format(
                    self.qty,
                    self.get_symbols()[0],
                    "%.2f" % (100 * (self.sell_target - self.buy_price) / self.buy_price),
                    "%.2f" % (self.time().now() - self.run_info.buy_time).total_seconds()
                ))
            self.stop_running(sell_price=self.sell_target)
            return

        # Dump the symbol when the market is nearing closing time
        if self.market_closes_soon():
            if self.waiting_for_next_offer():
                return
            self.sell_target = current_price * (1 + (0.05 / 100))
            if self.too_close_to_last_offer():
                return
            self.acct.place_limit_sell(self.get_symbols()[0], self.sell_target, self.qty)
            self.next_adjustment = self.time().now() + timedelta(seconds=20)
            self.info_process('ReCycleStrategy placing non-greedy offer since markets close soon: ${0}'
                              .format("%.2f" % self.sell_target))
            return

        # A) [y < -0.3%] Look ahead to cut losses (i.e. place a stop order) when the price dips low
        if current_price < self.buy_price * (1 - (0.3 / 100)):
            self.sell_target = self.stop_price
            if self.too_close_to_last_offer():
                return
            self.reset_cycle()
            self.acct.place_stop_order(self.get_symbols()[0], self.sell_target, self.qty)
            self.info_process(
                'ReCycleStrategy placing stop order at ${0}'.format("%.2f" % self.sell_target))
            return

        # B) [y < +0.12%] When the price is just under the break even point, place a modest limit-sell
        if current_price < self.buy_price * (1 + (0.12 / 100)):
            if self.waiting_for_next_offer():
                return
            self.sell_target = safety_sell_point
            if self.too_close_to_last_offer():
                return
            self.acct.place_limit_sell(self.get_symbols()[0], self.sell_target, self.qty)
            # Expire this order soon since it would give minimal profit
            self.next_adjustment = self.time().now() + timedelta(seconds=cycle_constants.BASELINE_OPEN_DURATION)
            self.info_process('ReCycleStrategy setting baseline sell order at ${0}'.format("%.2f" % self.sell_target))

        # C) [y > +0.12%] Run next cycle when the current one expires
        if not self.waiting_for_next_offer():
            self.start_next_cycle(current_price, safety_sell_point, greedy_sell_point)

    def insufficient_funds(self) -> bool:
        return self.acct.withdrawable_balance < cycle_constants.MIN_PURCHASE

    def not_bought_yet(self) -> bool:
        return self.run_info.buy_time is None and self.acct.positions is None

    def climbed_too_much(self) -> bool:
        return self.candles_5[-1].close >= self.buy_price * (
                1.0 + (cycle_constants.MAX_PCT_INCREASE_BEFORE_BUY / 100.0))

    def waited_too_long_for_dip(self) -> bool:
        return self.time().now() >= self.run_info.start_time + timedelta(seconds=cycle_constants.MAX_DIP_TIME)

    def symbol_was_sold(self) -> bool:
        return self.run_info.buy_time is not None and self.sell_target is not None and self.acct.positions is None

    def market_closes_soon(self) -> bool:
        return self.time().get_secs_to_close() < 60 * 45

    def waiting_for_next_offer(self) -> bool:
        return self.time().now() < self.next_adjustment

    def reset_cycle(self) -> None:
        self.times_lowered = 0
        self.next_adjustment = self.time().now()

    def start_next_cycle(self, current_price: float, safety_sell_point: float, greedy_sell_point: float) -> None:
        """Repeat a 5-step cycle while the price is minimally profitable or almost there."""
        self.times_lowered += 1
        if self.times_lowered == 6:
            self.times_lowered = 1

        # Determine the next cycle's price
        if self.times_lowered == 1:
            # Step 1: Make a greedy first offer
            self.sell_target = greedy_sell_point
            # Try to sell even higher than the target price if the current price is very high
            if current_price > greedy_sell_point * (1 - (0.1 / 100)):
                self.sell_target = self.sell_target + (self.buy_price * (1 + (0.08 / 100)))
        elif self.times_lowered <= 4:
            # Steps 2-4: Lower the offer 3 times, but not below safety_sell_point
            amt_to_lower_by = (greedy_sell_point - safety_sell_point) / 3.5
            self.sell_target -= amt_to_lower_by
        elif self.times_lowered == 5:
            # Step 5: Lower the offer to the lowest acceptable price
            self.sell_target = safety_sell_point

        # Determine the next cycle's lifetime
        if self.times_lowered == 1:
            self.next_adjustment = self.time().now() + timedelta(seconds=12)
        elif self.times_lowered == 2:
            self.next_adjustment = self.time().now() + timedelta(seconds=12)
        elif self.times_lowered == 3:
            self.next_adjustment = self.time().now() + timedelta(seconds=10)
        elif self.times_lowered == 4:
            self.next_adjustment = self.time().now() + timedelta(seconds=8)
        elif self.times_lowered == 5:
            self.next_adjustment = self.time().now() + timedelta(seconds=6)

        # Place order if price is valid
        if self.too_close_to_last_offer():
            self.info_process('ReCycleStrategy offer too close to last one. Not updating')
            return
        self.acct.place_limit_sell(self.get_symbols()[0], self.sell_target, self.qty)
        self.info_process('ReCycleStrategy Cycle #{0} price: ${1}  {2}'
                          .format(self.times_lowered, "%.2f" % self.sell_target, self.time().now().time()))

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
        self.candles_5.append(candle)
        if len(self.candles_5) <= 60 * 5:
            return
        oldest_candle = None
        for c in self.candles_5:
            if oldest_candle is None or c.moment < oldest_candle.moment:
                oldest_candle = c
        self.candles_5.remove(oldest_candle)

    def get_qty_at_price(self, price: float) -> int:
        """Return the max shares that can be bought at the given price per share."""
        shares = int(math.floor((self.max_purchase_pct() * self.acct.withdrawable_balance) / price))
        return min(shares,
                   int(math.floor(self.max_purchase_usd() / price)))
