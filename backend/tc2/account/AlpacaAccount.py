import math
import traceback
from datetime import timedelta, date, datetime
from typing import Optional, List
import time as pytime

import alpaca_trade_api as ata
import pandas as pd

from tc2.account.AbstractAccount import AbstractAccount
from tc2.account.data_stream.AccountDataStream import AccountDataStream
from tc2.account.data_stream.StreamUpdate import StreamUpdate
from tc2.account.data_stream.StreamUpdateType import StreamUpdateType
from tc2.data.data_structs.account_data.Order import Order
from tc2.data.data_structs.account_data.OrderStatus import OrderStatus
from tc2.data.data_structs.account_data.OrderType import OrderType
from tc2.data.data_structs.account_data.Position import Position
from tc2.data.data_structs.account_data.RoundTripTrade import RoundTripTrade
from tc2.env.ExecEnv import ExecEnv
from tc2.log.LogFeed import LogFeed


class AlpacaAccount(AbstractAccount):
    """
    Interacts with the Alpaca brokerage using their API.
    Do not create a new AlpacaAccount instance until calling shutdown() on the last instance.
    """

    # The list of round-trip trades made on the account.
    trade_history_loaded: List[str]

    # The client that facilitates calls to Alpaca.markets rest API.
    rest_client: ata.REST

    # The moment when a buy/sell order was last placed.
    last_buy_order_time: datetime
    last_sell_order_time: datetime

    # The list of stream updates shared between processes.
    livestream_updates: 'multiprocessing list'

    # The minimum time (in secs) to wait between placing two orders on the same side (buy/sell).
    ORDER_COOLDOWN = 0.5

    def __init__(self,
                 env: ExecEnv,
                 logfeed_trading: LogFeed,
                 livestream_updates: 'multiprocessing list') -> None:
        """
        Does NOT load trade history. This is done using load_trade_history().
        """
        super().__init__(env, logfeed_trading)

        # Private variables
        self.trade_history_loaded = []
        self.rest_client = ata.REST()
        self.last_buy_order_time = self.time().now() - timedelta(minutes=1)
        self.last_sell_order_time = self.time().now() - timedelta(minutes=1)
        self.livestream_updates = livestream_updates

        # Load balance info
        self.refresh_balance_info()

    def place_limit_buy(self, symbol: str, limit: float, qty: int) -> bool:
        # Ensure the strategy waits for a moment between placing orders
        while self.time().now() - self.last_buy_order_time <= timedelta(seconds=self.ORDER_COOLDOWN):
            self.warn_process('AlpacaAccount cooling down before placing next buy order.')
            pytime.sleep(0.2)

        try:
            limit = self.round_down(limit, 2)
            self.cancel_open_orders([symbol])
            pytime.sleep(0.2)
            self.rest_client.submit_order(symbol=symbol, qty=qty, side='buy', type='limit', limit_price=limit,
                                          time_in_force='day')
            self.last_buy_order_time = self.time().now()
        except Exception as e:
            self.error_process(f'Error placing limit-buy order on Alpaca for {qty} {symbol} at ${limit:.2f}:')
            self.warn_process(traceback.format_exc())
            return False
        return True

    def place_limit_sell(self, symbol: str, limit: float, qty: int) -> bool:
        # Ensure the strategy waits for a moment between placing orders
        while self.time().now() - self.last_sell_order_time <= timedelta(seconds=self.ORDER_COOLDOWN):
            self.warn_process('AlpacaAccount cooling down before placing next sell order.')
            pytime.sleep(0.2)

        try:
            limit = self.round_up(limit, 2)
            self.cancel_open_orders([symbol])
            pytime.sleep(0.2)
            self.rest_client.submit_order(symbol=symbol, qty=qty, side='sell', type='limit', limit_price=limit,
                                          time_in_force='day')
            self.last_sell_order_time = self.time().now()
        except Exception as e:
            self.error_process(f'Error placing limit-sell order on Alpaca for {qty} {symbol} at ${limit:.2f}:')
            self.warn_process(traceback.format_exc())
            return False
        return True

    def place_stop_order(self, symbol: str, price: float, qty: int) -> bool:
        try:
            price = self.round_down(price, 2)
            self.cancel_open_orders([symbol])
            pytime.sleep(0.2)
            self.rest_client.submit_order(symbol=symbol, qty=qty, side='sell', type='stop', time_in_force='day',
                                          stop_price=price)
        except Exception as e:
            self.error_process(f'Error placing stop order on Alpaca for {qty} {symbol} at ${price:.2f}:')
            self.warn_process(traceback.format_exc())
            return False
        return True

    def can_day_trade(self) -> bool:
        """Returns False if this account made too many day trades and lacks the $25k needed to be a PDT."""
        acct_response = self.rest_client.get_account()
        return int(acct_response.daytrade_count) <= 2 or float(acct_response.equity) > 28000

    def get_trade_history(self, symbol) -> List[RoundTripTrade]:
        if symbol not in self.trade_history_loaded:
            self.load_trade_history(symbol,
                                    self.time().now().date() - timedelta(days=2),
                                    self.time().now().date() + timedelta(days=1))
        return self.trade_history[symbol]

    def load_trade_history(self, symbol: str, start_date: date, end_date: date) -> None:
        """Gets up to 500 orders placed during the time window (exclusive) and parses them to find round-trip trades."""

        # Load trade history from redis
        self.trade_history[symbol] = self.redis().get_trade_history(symbols=[symbol])

        # Load recent orders from Alpaca
        # See https://docs.alpaca.markets/api-documentation/api-v2/orders/#get-a-list-of-orders
        order_entities = self.rest_client.list_orders(status='closed', limit=500, after=pd.Timestamp(start_date),
                                                      until=pd.Timestamp(end_date), direction='desc')
        orders = [Order.from_alpaca_api(order_ent._raw, self.logfeed_process) for order_ent in order_entities]

        # Parse orders for trades
        sell_order: Optional[Order] = None
        for order in orders:
            if order.status != OrderStatus.FILLED:
                continue
            if sell_order is None and order.type != OrderType.LIMIT_BUY:
                sell_order = order
            elif sell_order is not None and order.type == OrderType.LIMIT_BUY:
                trade = RoundTripTrade(order.get_symbol(),
                                       order.get_moment(),
                                       sell_order.get_moment(),
                                       order.get_price(),
                                       sell_order.get_price(),
                                       order.get_qty())
                # Store new trades
                if trade not in self.trade_history:
                    self.trade_history[symbol].append(trade)
                    self.redis().record_trade(trade)
                sell_order = None

        if symbol not in self.trade_history_loaded:
            self.trade_history_loaded.append(symbol)

    def cancel_open_orders(self,
                           symbols: List[str]) -> None:
        """See https://docs.alpaca.markets/api-documentation/api-v2/orders/#get-a-list-of-orders."""
        for order_ent in self.rest_client.list_orders():
            if order_ent.symbol not in symbols:
                continue
            self.warn_process(f'Canceling open order for {order_ent.symbol}')
            self.rest_client.cancel_order(order_ent.id)

    def liquidate_positions(self,
                            symbols: List[str]) -> None:
        # See https://docs.alpaca.markets/api-documentation/api-v2/positions/#position-entity
        for pos_ent in self.rest_client.list_positions():
            if pos_ent.symbol not in symbols:
                continue
            if int(pos_ent.qty) < 0:
                self.warn_process(f'Liquidating short position in {pos_ent.symbol}: dumping {int(pos_ent.qty)} shares')
                self.place_limit_buy(pos_ent.symbol, float(pos_ent.current_price) * 1.03, int(pos_ent.qty) * -1)
            else:
                self.warn_process(f'Liquidating position in {pos_ent.symbol}: dumping {int(pos_ent.qty)} shares')
                self.place_limit_sell(pos_ent.symbol, float(pos_ent.current_price) * 0.97, int(pos_ent.qty))

    def get_next_trading_update(self,
                                symbols: List[str],
                                strategy_start: Optional[datetime] = None) -> Optional[StreamUpdate]:
        while True:
            # Get the oldest unseen update from the stream.
            update_get_start = pytime.monotonic()
            update = self.stream_queue.get_next_update(
                master_queue=AccountDataStream.get_updates(self.livestream_updates),
                moment=self.time().now(),
                strategy_start=strategy_start if strategy_start else self.time().now() - timedelta(seconds=20),
                symbols=symbols)
            update_get_time_ms = (pytime.monotonic() - update_get_start) * 1000.0
            if update_get_time_ms > 50:
                # print(f'took {update_get_time_ms:.0f}ms to get update '
                #       f'(is unseen: {"yes" if update is not None else "no"})')
                pass
            if update is None:
                return None

            update_preprocess_start = pytime.monotonic()

            # Synchronize cached info if the stream just connected.
            if update.update_type is StreamUpdateType.STARTED_UP:
                self.refresh_balance_info()
                self.refresh_positions(symbols)
                self.refresh_open_orders(symbols)
                update_preprocess_time_ms = (pytime.monotonic() - update_preprocess_start) * 1000.0
                if update_preprocess_time_ms > 50:
                    print(f'took {update_preprocess_time_ms:.0f}ms to handle re-connecting to data streams')
                continue

            # Show the update to the account before the strategy.
            if update.update_type is StreamUpdateType.ACCT_INFO or update.get_symbol() in symbols:
                self.preprocess_stream_update(update)
                update_preprocess_time_ms = (pytime.monotonic() - update_preprocess_start) * 1000.0
                if update_preprocess_time_ms > 50:
                    print(f'took {update_preprocess_time_ms:.0f}ms to preprocess update')
                return update


    def refresh_balance_info(self) -> None:
        """
        See https://docs.alpaca.markets/api-documentation/api-v2/account/#account-entity.
        """
        acct_response = self.rest_client.get_account()
        if acct_response.status != 'ACTIVE':
            self.warn_main('Non-active Alpaca account status: {}'.format(acct_response.status))
        self.balance = acct_response.equity
        try:
            self.withdrawable_balance = float(acct_response.cash)
        except Exception:
            self.withdrawable_balance = 0

    def refresh_open_orders(self,
                            symbols: List[str]) -> None:
        """
        See https://docs.alpaca.markets/api-documentation/api-v2/orders/#get-a-list-of-orders.
        """
        try:
            self.open_orders = []
            for order_ent in self.rest_client.list_orders():
                order = Order.from_alpaca_api(order_ent, self.logfeed_process)
                if order.symbol in symbols and order.status == OrderStatus.OPEN:
                    self.open_orders.append(order)
        except Exception as e:
            self.error_process('Error refreshing open orders from alpaca rest api:')
            self.warn_process(traceback.format_exc())

    def refresh_positions(self,
                          symbols: List[str]) -> None:
        """
        See https://docs.alpaca.markets/api-documentation/api-v2/positions/#position-entity.
        """
        try:
            self.positions = []
            for pos_ent in self.rest_client.list_positions():
                if pos_ent.symbol in symbols:
                    self.positions.append(Position(pos_ent.symbol, int(pos_ent.qty)))
        except Exception as e:
            self.error_process('Error refreshing positions from alpaca rest api:')
            self.warn_process(traceback.format_exc())

    @staticmethod
    def round_up(value: float, precision: int):
        scale = int(precision ** 10)
        return math.ceil(value * scale) / scale

    @staticmethod
    def round_down(value: float, precision: int):
        scale = int(precision ** 10)
        return math.floor(value * scale) / scale
