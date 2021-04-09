from datetime import datetime
from typing import Optional, List, Dict

from tc2.account.data_stream.StreamUpdate import StreamUpdate
from tc2.account.data_stream.StreamUpdateQueue import StreamUpdateQueue
from tc2.account.data_stream.StreamUpdateType import StreamUpdateType
from tc2.data.data_structs.account_data.Order import Order
from tc2.data.data_structs.account_data.OrderStatus import OrderStatus
from tc2.data.data_structs.account_data.OrderType import OrderType
from tc2.data.data_structs.account_data.Position import Position
from tc2.data.data_structs.account_data.RoundTripTrade import RoundTripTrade
from tc2.env.ExecEnv import ExecEnv
from tc2.log.LogFeed import LogFeed


class AbstractAccount(ExecEnv):
    """
    The structure of a brokerage account class, which any simulated account class or real account class can
    implement and use to execute or back-test strategies.
    """

    stream_queue: StreamUpdateQueue
    balance: float
    withdrawable_balance: float
    positions: List[Position]
    open_orders: List[Order]

    def __init__(self,
                 env: ExecEnv,
                 logfeed_process: LogFeed) -> None:
        super().__init__(env.logfeed_program, logfeed_process)
        self.clone_same_thread(env)

        # Private variables
        self.trade_history: Dict[str, List[RoundTripTrade]] = {}

        # Public variables
        self.stream_queue = StreamUpdateQueue()
        self.balance = 0
        self.withdrawable_balance = 0
        self.open_orders = []
        self.positions = []

    def place_limit_buy(self, symbol: str, limit: float, qty: int) -> bool:
        """
        Logic must be handled by the overridden function of an inheriting class.
        The function must cancel any conflicting orders before placing the new one.
        """
        raise NotImplementedError

    def place_limit_sell(self, symbol: str, limit: float, qty: int) -> bool:
        """
        Logic must be handled by the overridden function of an inheriting class.
        The function must cancel any conflicting orders before placing the new one.
        """
        raise NotImplementedError

    def place_stop_order(self, symbol: str, price: float, qty: int) -> bool:
        """
        Logic must be handled by the overridden function of an inheriting class.
        The function must cancel any conflicting orders before placing the new one.
        """
        raise NotImplementedError

    def cancel_open_orders(self,
                           symbols: List[str]) -> None:
        """
        Cancels open orders associated with the given symbols.
        """
        raise NotImplementedError

    def liquidate_positions(self,
                            symbols: List[str]) -> None:
        """
        Liquidates (market-sells) positions in the given symbols.
        """
        raise NotImplementedError

    def get_next_trading_update(self,
                                symbols: List[str],
                                strategy_start: Optional[datetime] = None) -> Optional[StreamUpdate]:
        """
        Returns the first stream update that triggers strategy logic.
        """
        raise NotImplementedError

    def get_open_orders(self) -> List[Order]:
        """
        Returns a list of cached open order, not necessarily up-to-date.
        """
        return self.open_orders

    def get_positions(self) -> List[Position]:
        """
        Returns a list of cached positions held by the account, not necessarily up-to-date.
        """
        return self.positions

    def shutdown(self) -> None:
        return

    def preprocess_stream_update(self,
                                 update: StreamUpdate) -> None:
        """
        Pre-processes an update from the data stream before the strategy is informed.
        E.g. updates the account's balance when a balance update comes in.
        """

        # Update cached balance info.
        if update.update_type is StreamUpdateType.ACCT_INFO:
            acct_info = update.get_acct_info()
            self.debug_process(f'New acct balance: ${acct_info.cash:.2f} / ${acct_info.cash_withdrawable:.2f}')
            self.balance = acct_info.cash
            self.withdrawable_balance = acct_info.cash_withdrawable

        # Update cached open orders.
        if update.update_type is StreamUpdateType.ORDER:
            new_order = update.get_order()
            if new_order.get_status() == OrderStatus.FILLED:
                # Remove filled order from orders cache.
                # self.debug_process('Acct un-caching filled order: {}'.format(new_order.to_json()))
                self.open_orders = [order for order in self.open_orders if order.get_id() != new_order.get_id()]

                # Remove sold qty from positions cache.
                if new_order.get_type() in [OrderType.LIMIT_SELL, OrderType.MARKET_SELL, OrderType.STOP]:
                    sold_qty = new_order.get_qty()
                    assert isinstance(sold_qty, int)
                    for position in self.positions:
                        if position.symbol == new_order.symbol:
                            position.shares -= sold_qty
                    self.positions = [position for position in self.positions if position.shares != 0]

                # Add bought qty to positions cache.
                if new_order.get_type() in [OrderType.LIMIT_BUY, OrderType.MARKET_BUY]:
                    bought_qty = new_order.get_qty()
                    assert isinstance(bought_qty, int)
                    position_increased = False
                    for position in self.positions:
                        if position.symbol == new_order.symbol:
                            position.shares += bought_qty
                    if not position_increased:
                        self.positions.append(Position(symbol=new_order.symbol,
                                                       shares=bought_qty))
            else:
                # Add open order to orders cache.
                # self.debug_process('Acct caching new open order: {}'.format(new_order.to_json()))
                self.open_orders.append(new_order)

    # TODO Move to RedisManager
    def get_trade_history(self, symbol) -> list:
        """Returns a list of RoundTripTrade objects."""
        return self.trade_history[symbol]

    # TODO Move to RedisManager
    def get_trades_since(self, symbol: str, time: datetime) -> List[RoundTripTrade]:
        """Return a list of RoundTripTrade objects where the buy trade was made on or after :time:."""
        return self.get_trades_in_range(symbol, time, self.time().now())

    # TODO Move to RedisManager
    def get_trades_in_range(self, symbol: str, range_start: datetime, range_end: datetime) -> List[RoundTripTrade]:
        """Returns a list of RoundTrip objects executed in the given datetime range."""
        filtered_trades = []
        for trade in self.get_trade_history(symbol):
            if range_start <= trade.get_buy_time() <= range_end:
                filtered_trades.append(trade)
            return filtered_trades
