import traceback
import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from tc2.account.AbstractAccount import AbstractAccount
from tc2.account.data_stream.StreamUpdate import StreamUpdate
from tc2.account.data_stream.StreamUpdateType import StreamUpdateType
from tc2.data.data_structs.account_data.Order import Order
from tc2.data.data_structs.account_data.OrderStatus import OrderStatus
from tc2.data.data_structs.account_data.OrderType import OrderType
from tc2.data.data_structs.account_data.Position import Position
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.env.ExecEnv import ExecEnv
from tc2.log.LogFeed import LogFeed


class VirtualAccount(AbstractAccount):
    """
    Simulates having a brokerage account, but is time agnostic so that "live" trading can be simulated historically.
    One VirtualAccount instance required for each symbol being simulated.
    """

    start_time: datetime
    refresh_interval: int
    latest_candle: Optional[Candle]
    latest_updates: List[StreamUpdate]

    def __init__(self, sim_env: ExecEnv,
                 logfeed_process: LogFeed,
                 start_time: datetime,
                 refresh_interval: int = 105) -> None:

        super().__init__(sim_env, logfeed_process)

        # Private variables.
        self.start_time = start_time
        self.refresh_interval = refresh_interval
        self.latest_candle = None
        self.latest_updates = []

    def place_limit_buy(self, symbol: str, limit: float, qty: int) -> bool:
        # Create a fake order.
        order = Order(OrderType.LIMIT_BUY, OrderStatus.OPEN, symbol, limit, qty, str(uuid.uuid4()))
        # Remove open limit buy orders for the symbol.
        self.open_orders = [order for order in self.open_orders if
                            order.symbol != symbol or order.type != OrderType.LIMIT_BUY]
        # Add the new order.
        self.open_orders.append(order)
        return True

    def place_limit_sell(self, symbol: str, limit: float, qty: int) -> bool:
        # Create a fake order.
        order = Order(OrderType.LIMIT_SELL, OrderStatus.OPEN, symbol, limit, qty, str(uuid.uuid4()))
        # Remove open limit sell orders for the symbol.
        self.open_orders = [order for order in self.open_orders if
                            order.symbol != symbol or order.type != OrderType.LIMIT_SELL]
        # Add the new order.
        self.open_orders.append(order)
        return True

    def place_stop_order(self, symbol: str, price: float, qty: int) -> bool:
        # Create a fake order.
        order = Order(OrderType.STOP, OrderStatus.OPEN, symbol, price, qty, str(uuid.uuid4()))
        # Remove open stop orders for the symbol.
        self.open_orders = [order for order in self.open_orders if
                            order.symbol != symbol or order.type != OrderType.STOP]
        # Add the new order.
        self.open_orders.append(order)
        return True

    def cancel_open_orders(self,
                           symbols: List[str]) -> None:
        self.open_orders = [order for order in self.open_orders if order.symbol in symbols]

    def liquidate_positions(self,
                            symbols: List[str]) -> None:
        self.positions = [position for position in self.positions if position.symbol not in symbols]

    def refresh_acct(self,
                     virtual_time: datetime,
                     day_data: SymbolDay) -> None:
        """
        Simulates checking a brokerage stream for account and market data updates.
        Must be called by a StrategySimulator class.
        """

        # Get the "latest" price from mongo data
        latest_candle: Optional[Candle] = None
        for candle in day_data.candles:
            if virtual_time - timedelta(milliseconds=900) <= candle.moment < virtual_time + timedelta(milliseconds=900):
                latest_candle = candle
                break

        if latest_candle is None:
            return

        # self.debug_process(f'Refreshing virtual acct with {day_data.symbol}\'s candle at '
        #                    f'{latest_candle.moment:%H:%M:%S}')

        try:
            # Simulate orders being filled on the market and returned via the data stream.
            for open_order in self.open_orders:
                if open_order.symbol != day_data.symbol:
                    continue

                prev_status_times_2 = open_order.status.value * 2
                if open_order.type is OrderType.STOP and latest_candle.low < open_order.price:
                    open_order.status = OrderStatus.FILLED

                elif open_order.type is OrderType.LIMIT_BUY \
                        and open_order.price > 0.85 * latest_candle.open + 0.15 * latest_candle.high \
                        and open_order.qty < 2 * latest_candle.volume:
                    open_order.status = OrderStatus.FILLED

                elif open_order.type is OrderType.LIMIT_SELL \
                        and open_order.price < 0.85 * latest_candle.open + 0.15 * latest_candle.low \
                        and open_order.qty < 2 * latest_candle.volume:
                    open_order.status = OrderStatus.FILLED

                # Simulate streaming by the broker of the new order info
                if prev_status_times_2 != open_order.status.value * 2:
                    self.latest_updates.append(StreamUpdate(update_moment=virtual_time,
                                                            update_type=StreamUpdateType.ORDER,
                                                            symbol=open_order.symbol,
                                                            order=open_order.to_json()))

            # Simulate streaming by the broker of the new price info
            # self.debug_process(f'Adding candle update to simulated stream: ${latest_candle.open:.2f}')
            self.latest_updates.append(StreamUpdate(update_moment=virtual_time,
                                                    update_type=StreamUpdateType.CANDLE,
                                                    symbol=day_data.symbol,
                                                    candle=latest_candle.to_json()))
        except Exception as e:
            self.error_process(f'Error simulating the checking of brokerage data stream:')
            self.warn_process(traceback.format_exc())

    def get_next_trading_update(self,
                                symbols: List[str],
                                strategy_start: Optional[datetime] = None) -> Optional[StreamUpdate]:
        while True:
            # Get the oldest unseen update from the stream.
            update = self.stream_queue.get_next_update(master_queue=self.latest_updates,
                                                       moment=self.time().now(),
                                                       strategy_start=strategy_start)

            if update is None:
                return None
            # self.debug_process(f'Simulated fetching stream update: {update.to_json()}')

            # Show the update to the account before the strategy.
            self.preprocess_stream_update(update)

            # Return the first update that will advance strategy logic.
            if (update.update_type is StreamUpdateType.CANDLE or
                update.update_type is StreamUpdateType.ORDER) \
                    and update.get_symbol() in symbols:
                return update
