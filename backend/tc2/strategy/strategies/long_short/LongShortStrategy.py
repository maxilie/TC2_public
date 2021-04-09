from datetime import datetime, time
from statistics import mean
from typing import Dict, List, Optional

from tc2.data.data_structs.account_data.Order import Order
from tc2.data.data_structs.account_data.OrderStatus import OrderStatus
from tc2.data.data_structs.account_data.OrderType import OrderType
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.env.ExecEnv import ExecEnv
from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.stock_analysis.strategy_models.long_short_strategy.LongShortFavor import LongShortFavor
from tc2.strategy.AbstractStrategy import AbstractStrategy
from tc2.strategy.strategies.long_short.LongShortStep import LongShortStep
from tc2.strategy.strategies.long_short.longshort_constants import DUMP_WINDOW_SECS, FINAL_OPTIMISM_TIME, \
    FIRST_BUY_OR_SECOND_SALE_WAIT_TIME, \
    INITIAL_BUY_WAIT_TIME, KILLSWITCH_ACTIVATION_PCT, NEGOTIATION_TIME, SPXL_BUY_DIP_PCT, \
    SPXL_INITIAL_PROFIT_TARGET_PCT, SPXL_MAX_PROFIT_TARGET_PCT, SPXL_SPXS_SIZE
from tc2.util.TimeInterval import TimeInterval


class LongShortStrategy(AbstractStrategy):
    """
    A strategy whereby we buy SPXL and SPXS and sell each at a tiny profit.
    This strategy can be used when the S&P-500 is oscillating around a baseline, and not trending up or down.
    """

    @classmethod
    def times_active(cls) -> TimeInterval:
        return TimeInterval(logfeed=None,
                            start1=time(hour=10, minute=30),
                            end1=time(hour=14, minute=45))

    @classmethod
    def pass_fail_models(cls) -> List[AnalysisModelType]:
        return [
            AnalysisModelType.LS_FAVOR,
            AnalysisModelType.OSCILLATION
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
        return False

    # Current step along the strategy logic's path.
    current_step: LongShortStep

    # Moment when execution of the current step began.
    current_step_start_time: datetime

    # Latest stock prices.
    spxl_price: float = None
    spxs_price: float = None

    # Recent stock prices.
    spxl_prev_5_candles = []
    spxs_prev_5_candles = []

    # Markers for initial buy attempts.
    printed_spxl_buy_start: bool = False
    printed_spxs_buy_start: bool = False

    # Number of shares bought or attempted.
    spxl_shares: int = None
    spxs_shares: int = None

    # Final, actual buy prices.
    spxl_buy_price: Optional[float] = None
    spxs_buy_price: Optional[float] = None

    # Markers for initial sell attempts.
    printed_spxl_sell_start: bool = False
    printed_spxs_sell_start: bool = False

    # Initial targeted sell prices.
    spxl_initial_target: float = None
    spxs_initial_target: float = None

    # Lowered sell price targets.
    spxl_adj_target: Optional[float] = None
    spxs_adj_target: Optional[float] = None

    # Final, actual sell prices.
    spxl_sell_price: Optional[float] = None
    spxs_sell_price: Optional[float] = None

    # Whether each symbol was sold.
    spxl_sold: bool = False
    spxs_sold: bool = False

    def __init__(self,
                 env: ExecEnv,
                 symbols: List[str]) -> None:
        """
        :param symbols: is irrelevant since this strategy always trades SPY, SPXL, SPXS.
        """
        super().__init__(env=env,
                         symbols=['SPY', 'SPXL', 'SPXS'])
        self.current_step = LongShortStep.WAIT_FOR_DATA
        self.current_step_start_time = self.time().now()

    def on_new_info(self,
                    symbol: str,
                    moment: datetime,
                    candle: Optional[Candle] = None,
                    order: Optional[Order] = None) -> None:

        # Ignore updates on other symbols.
        if symbol != 'SPXL' and symbol != 'SPXS':
            return

        # Print the candle or order
        self.print_debug(symbol, moment, candle, order)

        # Update price variables.
        if candle is not None:
            if symbol == 'SPXL':
                self.spxl_price = candle.close
                self.spxl_prev_5_candles.append(candle)
                self.spxl_prev_5_candles = self.spxl_prev_5_candles[-5:]
            elif symbol == 'SPXS':
                self.spxs_price = candle.close
                self.spxs_prev_5_candles.append(candle)
                self.spxs_prev_5_candles = self.spxs_prev_5_candles[-5:]

        # Run the next logical step(s) in the strategy.
        steps = {
            LongShortStep.WAIT_FOR_DATA:                     self.wait_for_data,
            LongShortStep.ENTER_SPXS_SPXL:                   self.enter_spxs_spxl,
            LongShortStep.WAIT_FOR_SINGLE_BUY:               self.wait_for_single_buy,
            LongShortStep.SELL_FIRST_POS_AT_PROFIT:          self.sell_first_pos_at_profit,
            LongShortStep.WAIT_FOR_FIRST_SALE_OR_SECOND_BUY: self.wait_for_first_sale_or_second_buy,
            LongShortStep.LOWER_SALES_TO_BASELINE:           self.lower_sales_to_baseline,
            LongShortStep.SELL_AT_MINOR_LOSS:                self.sell_at_minor_loss,
        }
        for step_name, step_logic in steps.items():
            if self.current_step is step_name and self.is_running():
                self.debug_process(f'LongShortStrategy running step: {step_name.name}')
                step_logic(symbol, moment, candle, order)
                self.debug_process(f'LongShortStrategy finished step: {step_name.name}')

    def buy_logic(self) -> None:
        pass

    def sell_logic(self) -> None:
        pass

    def print_debug(self, symbol, moment, candle, order):
        """
        For debugging purposes, print every new price and order status as they come in.
        """
        if order is not None:
            self.info_process('')
            self.info_process('')
            self.info_process(f'LongShortStrategy: {order.get_type().name} order new status is '
                              f'{order.get_status().name} for {order.get_qty()} {order.get_symbol()} at '
                              f'${order.get_price():.2f}')
        elif candle is not None:
            self.info_process('')
            self.info_process('')
            self.info_process(f'LongShortStrategy: ${candle.close:.2f} at {candle.moment:%H:%M:%S} for {symbol}')
        else:
            self.info_process('')
            self.info_process('')
            self.warn_process(f'LongShortStrategy: Received an update call, but candle and order are null')

    def check_for_purchases(self, order):
        """
        Updates variables with purchase info and prints the purchase.
        Returns True if a buy order was processed, False otherwise.
        """
        if order is not None and order.get_type() is OrderType.LIMIT_BUY and order.get_status() is OrderStatus.FILLED:
            if order.get_symbol() == 'SPXS':
                self.spxs_buy_price = order.get_price()
                self.run_info.record_purchase(symbol='SPXS', price=self.spxs_buy_price, qty=order.get_qty(),
                                              moment=order.get_moment())
                self.info_process(f'LongShortStrategy: SPXS was bought for ${self.spxs_buy_price:.2f}')
                return True
            elif order.get_symbol() == 'SPXL':
                self.spxl_buy_price = order.get_price()
                self.run_info.record_purchase(symbol='SPXL', price=self.spxl_buy_price, qty=order.get_qty(),
                                              moment=order.get_moment())
                self.info_process(f'LongShortStrategy: SPXL was bought for ${self.spxl_buy_price:.2f}')
                return True
        return False

    def check_for_sales(self, order):
        """
        Updates variables with sale info and prints the sale.
        Returns True if a sell order was processed, False otherwise.
        """
        if order is not None and order.get_status() == OrderStatus.FILLED and order.get_type() == OrderType.LIMIT_SELL:
            if order.get_symbol() == 'SPXS':
                self.spxs_sell_price = order.get_price()
                self.spxs_sold = True
                self.run_info.record_sale(symbol='SPXS', price=self.spxs_sell_price, qty=order.get_qty(),
                                          moment=order.get_moment())
                self.info_process(f'LongShortStrategy: SPXS was sold for ${self.spxs_sell_price:.2f}')
                return True
            elif order.get_symbol() == 'SPXL':
                self.spxl_sell_price = order.get_price()
                self.spxl_sold = True
                self.run_info.record_sale(symbol='SPXL', price=self.spxl_sell_price, qty=order.get_qty(),
                                          moment=order.get_moment())
                self.info_process(f'LongShortStrategy: SPXL was sold for ${self.spxl_sell_price:.2f}')
                return True
        return False

    """
    Strategy execution steps...
    """

    def wait_for_data(self, symbol, moment, candle, order):
        """
        STEP 1: Wait to buy until we have the latest prices.
        """

        if self.spxl_price is None or len(self.spxl_prev_5_candles) <= 3 or self.spxs_price is None or len(
                self.spxs_prev_5_candles) <= 3:
            self.info_process('LongShortStrategy waiting for more price data on the symbols...')
        else:
            self.next_step(LongShortStep.ENTER_SPXS_SPXL)

    def enter_spxs_spxl(self, symbol, moment, candle, order):
        """
        STEP 2: Place slightly low-ball buy orders for both SPXS and SPXL.

        This ensures we enter a position with a good chance of getting out at a profit.
        """

        # Move to the next step once SPXS and SPXL buy orders have been placed.
        if self.printed_spxs_buy_start and self.printed_spxl_buy_start:
            self.next_step(LongShortStep.WAIT_FOR_SINGLE_BUY)

        # Buy SPXS.
        if not self.printed_spxs_buy_start:

            # Attempt to buy SPXS at or below its current price (this usually takes minutes to go through).
            spxs_recent_lowest_high = min([candle.high for candle in self.spxs_prev_5_candles])
            spxs_recent_low = min([candle.low for candle in self.spxs_prev_5_candles])
            spxs_target_buy = spxs_recent_low + 0.01
            if spxs_target_buy >= spxs_recent_lowest_high - 0.01:
                spxs_target_buy -= 0.01

            # Buy extra shares if analysis models predict a negative trend in the S&P-500.
            favor_multiplier = {
                LongShortFavor.SPXS_FAVORED:          1.08,
                LongShortFavor.SPXS_STRONGLY_FAVORED: 1.13,
            }
            self.spxs_shares = int(SPXL_SPXS_SIZE // spxs_target_buy) \
                               * favor_multiplier.get(self.get_model_output(AnalysisModelType.LS_FAVOR, 'SPXS'), 1)

            # Place the order.
            if self.acct.place_limit_buy('SPXS', spxs_target_buy, self.spxs_shares):
                self.info_process(f'LongShortStrategy buying SPXS at ${spxs_target_buy:.2f}')
                self.printed_spxs_buy_start = True
            else:
                self.warn_process(f'LongShortStrategy ending after buy order failed')
                self.stop_running(sell_price=None)
                return

        # Buy SPXL.
        if not self.printed_spxl_buy_start:

            # Attempt to buy SPXL just below its current price (this usually goes through quickly).
            spxl_target_buy = self.spxl_price - max(0.01, self.spxl_price * (SPXL_BUY_DIP_PCT / 100.0))

            # Ensure SPXL buy offer is not too low.
            # Raise it halfway to lowest price in the past 2 seconds.
            spxl_recent_low = min([prev_candle.low for prev_candle in self.spxl_prev_5_candles])
            if spxl_target_buy <= spxl_recent_low + 0.02:
                spxl_target_buy += (spxl_recent_low + 0.02 - spxl_target_buy) / 2.0

            # Buy extra shares if analysis models predict a negative trend in the S&P-500.
            favor_multiplier = {
                LongShortFavor.SPXL_FAVORED:          1.09,
                LongShortFavor.SPXL_STRONGLY_FAVORED: 1.14,
            }
            self.spxl_shares = int(SPXL_SPXS_SIZE // spxl_target_buy) \
                               * favor_multiplier.get(self.get_model_output(AnalysisModelType.LS_FAVOR, 'SPXL'), 1)

            # Place the order.
            if self.acct.place_limit_buy('SPXL', spxl_target_buy, self.spxl_shares):
                self.info_process(f'LongShortStrategy buying SPXL at ${spxl_target_buy:.2f}')
                self.printed_spxl_buy_start = True
            else:
                self.warn_process(f'LongShortStrategy ending after buy order failed')
                self.stop_running(sell_price=None)
                return

    def wait_for_single_buy(self, symbol, moment, candle, order):
        """
        STEP 3: Wait for either SPXS or SPXL buy order to go through.

        This means we can can profit off of one position without waiting for both
         buy orders to go through, since waiting for both takes longer, and that
         extra time increases the likelihood of one position declining significantly.
        """

        # Liquidate positions and end the strategy if neither buy order fills quickly.
        if self.get_time_this_step() > INITIAL_BUY_WAIT_TIME:
            self.acct.cancel_open_orders(symbols=self.get_symbols())
            self.acct.liquidate_positions(symbols=self.get_symbols())
            self.info_process('LongShortStrategy stopping because neither buy order got filled')
            self.stop_running(sell_price=None)
            return

        # Move to the next step once we know the order's official buy price.
        if self.check_for_purchases(order):
            self.next_step(LongShortStep.SELL_FIRST_POS_AT_PROFIT)

    def sell_first_pos_at_profit(self, symbol, moment, candle, order):
        """
        STEP 4: Sell our position at a tiny profit.

        This leads to the possibility of quickly selling one position at a profit
         without needing to enter the other position at all.
        """

        # Move to the next step on the first update AFTER placing the sell order.
        if self.printed_spxl_sell_start or self.printed_spxs_sell_start:
            self.next_step(LongShortStep.WAIT_FOR_FIRST_SALE_OR_SECOND_BUY)
            return

        # Place initial limit sell order for the position (SPXS).
        if self.spxs_buy_price is not None and not self.printed_spxs_sell_start:
            self.spxs_initial_target = self.spxs_buy_price + 0.01
            if self.acct.place_limit_sell('SPXS', self.spxs_initial_target, self.spxs_shares):
                self.info_process(f'Placed initial SPXS sell order for ${self.spxs_initial_target:.2f} (1 cent profit)')
                self.printed_spxs_sell_start = True
            else:
                self.warn_process(f'LongShortStrategy ending after sell order failed')
                self.stop_running(sell_price=None)
                return

        # Place initial limit sell order for the position (SPXL).
        if self.spxl_buy_price is not None and not self.printed_spxl_sell_start:
            self.spxl_initial_target = self.spxl_buy_price + \
                                       max(0.01, self.spxl_price * (SPXL_INITIAL_PROFIT_TARGET_PCT / 100.0))
            if self.acct.place_limit_sell('SPXL', self.spxl_initial_target, self.spxl_shares):
                self.info_process(
                    f'Placed initial SPXL sell order for ${self.spxl_initial_target:.2f} '
                    f'({SPXL_INITIAL_PROFIT_TARGET_PCT:.2f}% profit)')
                self.printed_spxl_sell_start = True
            else:
                self.warn_process(f'LongShortStrategy ending after sell order failed')
                self.stop_running(sell_price=None)
                return

        # Lower existing buy offer on SPXL.
        # SPXL is more volatile, so we want to capture SPXL profits while waiting for SPXS to sell.
        if self.spxs_buy_price is not None and self.spxl_buy_price is None:
            spxl_target_buy = self.spxl_price - max(0.01, self.spxl_price * (SPXL_BUY_DIP_PCT / 2 / 100.0))

            # Adjust the order down.
            if self.acct.place_limit_buy('SPXL', spxl_target_buy, self.spxl_shares):
                self.info_process(f'LongShortStrategy lowering SPXL buy  offer to ${spxl_target_buy:.2f}')
                self.printed_spxl_buy_start = True
            else:
                self.warn_process(f'LongShortStrategy ending after buy order failed')
                self.stop_running(sell_price=None)
                return

    def wait_for_first_sale_or_second_buy(self, symbol, moment, candle, order):
        """
        STEP 5: Wait for SPXL/SPXS to be bought or SPXS/SPXL to be sold, whichever happens first.

        This means that if our position profits, we capture those profits and get out - and
         if the value of our position declines, we now have the possibility of profiting
         from the new position.
        """

        # Liquidate positions and end the strategy if our buy order never gets filled.
        if self.get_time_this_step() > FIRST_BUY_OR_SECOND_SALE_WAIT_TIME:
            self.next_step(LongShortStep.LOWER_SALES_TO_BASELINE)
            return

        # Automatically sell off position(s) if the price drops too low.
        if self.check_and_run_killswitch() is not None:
            return

        # Move to the next step if both positions have been bought.
        if self.check_for_purchases(order):
            assert self.spxl_buy_price is not None and self.spxs_buy_price is not None
            self.next_step(LongShortStep.LOWER_SALES_TO_BASELINE)
            return

        # End the strategy if our only position sells.
        if self.check_for_sales(order):
            assert self.spxl_sold or self.spxs_sold
            self.info_process(f'Ending strategy after selling {"SPXL" if self.spxl_sold else "SPXS"} at a profit')
            self.acct.cancel_open_orders(symbols=self.get_symbols())
            self.acct.liquidate_positions(symbols=self.get_symbols())
            self.stop_running(sell_price=self.spxl_sell_price if self.spxl_sold else self.spxs_sell_price)
            return

    def lower_sales_to_baseline(self, symbol, moment, candle, order):
        """
        STEP 6: Gradually lower our sell offer(s) until one of them goes through.

        This step gives ample time for both greedy and reasonable offers alike to stand.
        But if they're not going through or one position already produced profits, the
         offers will eventually be lowered to non-profitable levels so we can avoid
         loss on at least one position.
        """

        # Sell at a loss if negotiation failed.
        if self.get_time_this_step() >= NEGOTIATION_TIME:
            # Ensure that we are not buying any more positions.
            if self.spxl_buy_price is None or self.spxs_buy_price is None:
                open_buy_symbol = 'SPXL' if self.spxl_buy_price is None else 'SPXS'
                self.info_process(f'LongShortStrategy canceling remaining buy order for {open_buy_symbol}')
                self.acct.cancel_open_orders(symbols=[open_buy_symbol])
            self.next_step(LongShortStep.SELL_AT_MINOR_LOSS)
            return

        # Check if our second buy order got filled.
        self.check_for_purchases(order)

        # Set max target sell price for SPXS.
        if self.spxs_buy_price is not None and self.spxs_initial_target is None:
            self.spxs_initial_target = self.spxs_buy_price + 0.01

        # Set max target sell price for SPXL.
        if self.spxl_buy_price is not None and self.spxl_initial_target is None:
            self.spxl_initial_target = self.spxl_buy_price + 0.01 + (
                    SPXL_MAX_PROFIT_TARGET_PCT / 100) * self.spxl_buy_price

        # Move to the next step once the first sell order gets filled.
        if self.check_for_sales(order):
            assert self.spxl_sold or self.spxs_sold
            # Ensure that we are not buying any more positions.
            if self.spxl_buy_price is None or self.spxs_buy_price is None:
                open_buy_symbol = 'SPXL' if self.spxl_buy_price is None else 'SPXS'
                self.info_process(f'LongShortStrategy canceling remaining buy order for {open_buy_symbol}')
                self.acct.cancel_open_orders(symbols=[open_buy_symbol])
            self.next_step(LongShortStep.SELL_AT_MINOR_LOSS)
            return

        # Automatically sell off position(s) if the price drops too low.
        if self.check_and_run_killswitch() is not None:
            return

        # Calculate linear time delay (as time goes up, offer_pct goes down).
        offer_pct = (NEGOTIATION_TIME - self.get_time_this_step()) / NEGOTIATION_TIME

        # Lower SPXL sell offer.
        if self.spxl_buy_price is not None and not self.spxl_sold:
            spxl_profit_amt = offer_pct * (self.spxl_initial_target - self.spxl_buy_price)
            next_spxl_offer = self.spxl_buy_price + 0.01 + spxl_profit_amt
            if self.spxl_adj_target is None or self.spxl_adj_target - next_spxl_offer >= 0.01:
                self.spxl_adj_target = next_spxl_offer
                self.acct.place_limit_sell('SPXL', self.spxl_adj_target, self.spxl_shares)
                self.info_process(f'LongShortStrategy adjusted SPXL offer to ${self.spxl_adj_target:.2f}')

        # Lower SPXS sell offer.
        if self.spxs_buy_price is not None and not self.spxs_sold:
            next_spxs_offer = self.spxs_buy_price + (0 if offer_pct < 0.5 else 0.01)
            if self.spxs_adj_target is None or self.spxs_adj_target - next_spxs_offer >= 0.01:
                self.spxs_adj_target = next_spxs_offer
                self.acct.place_limit_sell('SPXS', self.spxs_adj_target, self.spxs_shares)
                self.info_process(f'LongShortStrategy adjusted SPXS offer to ${self.spxs_adj_target:.2f}')

    def sell_at_minor_loss(self, symbol, moment, candle, order):
        """
        STEP 7: Sell the remaining position for what we bought it, if possible.
                Otherwise, sell it at market price.

        This makes sure we can minimize or even avoid losses on the second position.
        """

        # End the strategy if the remaining sell order gets filled.
        symbol_previously_held = 'SPXL' if not self.spxl_sold else 'SPXS'
        if self.check_for_sales(order):
            if symbol_previously_held == 'SPXL' and \
                    (self.spxs_buy_price is None or self.spxs_sold):
                self.debug_process(f'Ending strategy after selling SPXL.')
                self.stop_running(self.spxl_sell_price)
                return
            if symbol_previously_held == 'SPXS' and \
                    (self.spxl_buy_price is None or self.spxl_sold):
                self.debug_process(f'Ending strategy after selling SPXS.')
                self.stop_running(self.spxs_sell_price)
                return

        # Automatically sell off the position if the price drops too low.
        if self.check_and_run_killswitch() is not None:
            return

        # Lower outstanding sell offer to latest price (SPXL).
        if self.spxl_buy_price is not None and not self.spxl_sold:
            real_spxl_low = max([prev_candle.low for prev_candle in self.spxl_prev_5_candles])
            print(f'Real spxl low: ${real_spxl_low:.2f}  (bought at ${self.spxl_buy_price:.2f})')
            next_spxl_offer = min(mean([real_spxl_low, self.spxl_price]), mean([self.spxl_buy_price, self.spxl_price]))

            # Raise outstanding sell offer slightly if current price is close to buy price (SPXL).
            if self.get_time_this_step() < FINAL_OPTIMISM_TIME and \
                     self.spxl_buy_price * ((1 - 0.06) / 100) <= real_spxl_low:
                next_spxl_offer = self.spxl_buy_price + 0.03

            # Place adjusted sell order (SPXL).
            if self.spxl_adj_target is None or self.spxl_adj_target - next_spxl_offer >= 0.01:
                self.spxl_adj_target = next_spxl_offer
                self.acct.place_limit_sell('SPXL', self.spxl_adj_target, self.spxl_shares)
                self.info_process(f'LongShortStrategy adjusted SPXL offer to ${self.spxl_adj_target:.2f}')

        # Lower outstanding sell offer to latest price (SPXS).
        if self.spxs_buy_price is not None and not self.spxs_sold:
            real_spxs_low = max([prev_candle.low for prev_candle in self.spxs_prev_5_candles])
            print(f'Real spxs low: ${real_spxs_low:.2f}  (bought at ${self.spxs_buy_price:.2f})')
            next_spxs_offer = min(real_spxs_low, self.spxs_buy_price)

            # Raise outstanding sell offer slightly if current price is close to buy price (SPXS).
            if self.get_time_this_step() < FINAL_OPTIMISM_TIME and \
                    self.spxs_buy_price <= real_spxs_low + 0.01:
                next_spxs_offer = self.spxs_buy_price

            # Place adjusted sell order (SPXS).
            if self.spxs_adj_target is None or self.spxs_adj_target - next_spxs_offer >= 0.01:
                self.spxs_adj_target = next_spxs_offer
                self.acct.place_limit_sell('SPXS', self.spxs_adj_target, self.spxs_shares)
                self.info_process(f'LongShortStrategy adjusted SPXS offer to ${self.spxs_adj_target:.2f}')

    """
    Private util methods...
    """

    def get_time_this_step(self) -> float:
        """
        Returns the number of seconds elapsed since this step started.
        """
        return (self.time().now() - self.current_step_start_time).total_seconds()

    def next_step(self,
                  next_step: LongShortStep) -> None:
        """
        Moves to then next step and resets the timer.
        """
        self.current_step = next_step
        self.current_step_start_time = self.time().now()

    def check_and_run_killswitch(self) -> Optional[str]:
        """
        Returns None, or the symbol that was sold because it declined
            in price too much.
        """

        # Define method to sell off our losing shares.
        def run_killswitch(symbol, latest_price, shares_held):
            sell_price = latest_price - max(0.01, latest_price * 0.01)
            self.info_process(f'Killswitch activated on {symbol}. Selling at ${sell_price:.2f}')
            self.acct.place_limit_sell(symbol, sell_price, shares_held)

        # Define method to determine whether to sell off losing shares.
        def killswitch_activated(buy_price, latest_price) -> bool:
            pct_loss = (1.0 * buy_price - latest_price) / buy_price
            return pct_loss >= KILLSWITCH_ACTIVATION_PCT or self.time().get_secs_to_close() < DUMP_WINDOW_SECS

        # Sell off SPXL if necessary.
        if self.spxl_buy_price is not None and not self.spxl_sold \
                and killswitch_activated(self.spxl_buy_price, self.spxl_price):
            run_killswitch('SPXL', self.spxl_price, self.spxl_shares)
            return 'SPXL'

        # Sell off SPXS if necessary.
        if self.spxs_buy_price is not None and not self.spxs_sold \
                and killswitch_activated(self.spxs_buy_price, self.spxs_price):
            run_killswitch('SPXS', self.spxs_price, self.spxs_shares)
            return 'SPXS'

        # Return None if killswitch was not activated.
        return None
