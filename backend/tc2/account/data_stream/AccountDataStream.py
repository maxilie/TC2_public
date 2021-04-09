import asyncio
import multiprocessing
import time as pytime
import traceback
from ctypes import c_bool
from datetime import datetime
from threading import Thread
from typing import List

from alpaca_trade_api import StreamConn

from tc2.account.data_stream.StreamUpdate import StreamUpdate
from tc2.account.data_stream.StreamUpdateType import StreamUpdateType
from tc2.data.data_structs.account_data.AccountInfo import AccountInfo
from tc2.data.data_structs.account_data.Order import Order
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.log.LogFeed import LogFeed, LogLevel
from tc2.util.date_util import DATE_TIME_FORMAT


class AccountDataStream:
    """
    Connects to Alpaca and Polygon data streams and provides data access to AbstractAccount's.
    """

    # StreamConn from alpaca-trade-api library.
    alpaca_stream: StreamConn = None

    # Stream listener state (true until program is stopped).
    running = True

    # Thread-sharable list containing data updates.
    _livestream_updates: 'multiprocessing list' = None

    # Marker to know when to prune the updates list.
    _queue_initially_filled = multiprocessing.Value(c_bool, False)

    @classmethod
    def get_updates(cls,
                    livestream_updates: 'multiprocessing list') -> List[StreamUpdate]:
        return [StreamUpdate.from_json(update_json) for update_json in livestream_updates]

    @classmethod
    def connect_to_streams(cls,
                           symbols: List[str],
                           logfeed_data: LogFeed) -> None:
        """
        Starts a thread that listens for alpaca and polygon data streams.
        """

        # Initialize multi-threaded access to data updates.
        if cls._livestream_updates is not None:
            logfeed_data.log(LogLevel.ERROR, 'Tried to connect to account data streams twice!')
            print('Tried to connect to account data streams twice!')
            return
        cls._livestream_updates = multiprocessing.Manager().list()
        cls._queue_initially_filled = multiprocessing.Value(c_bool, False)

        # Define off-thread logic for handling stream messages.
        def init_streams():

            while cls.running:
                try:
                    # Create a new event loop for this thread.
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # From alpaca-trade-api.
                    cls.alpaca_stream = StreamConn(data_stream='polygon')

                    @cls.alpaca_stream.on(r'^trade_updates$')
                    async def on_trade_updates(conn, channel, data):
                        # logfeed_data.log(LogLevel.DEBUG, 'Alpaca raw trade update: {0}'.format(data))
                        try:
                            print('receiving order from ws')
                            order = Order.from_alpaca_api(data.order, logfeed_data)
                            if order is None:
                                logfeed_data.log(LogLevel.WARNING, 'Data stream could not decode an order. Ignoring it')
                                print('Data stream could not decode an order. Ignoring it')
                                cls._queue_update(moment=datetime.now(),
                                                  update_type=StreamUpdateType.STARTED_UP)
                            else:
                                cls._on_trade_update(order)
                        except Exception as e:
                            logfeed_data.log(LogLevel.ERROR, 'Error handling alpaca trade update:')
                            logfeed_data.log(LogLevel.WARNING, traceback.format_exc())
                            traceback.print_exc()

                    @cls.alpaca_stream.on(r'^account_updates$')
                    async def on_account_updates(conn, channel, msg):
                        logfeed_data.log(LogLevel.DEBUG, 'Alpaca raw account update: {0}'.format(msg))
                        print('Alpaca raw account update: {0}'.format(msg))
                        try:
                            print('receiving acct update from ws')
                            cls._on_account_update(msg, logfeed_data)
                        except Exception as e:
                            logfeed_data.log(LogLevel.ERROR, 'Error handling alpaca account update: ')
                            logfeed_data.log(LogLevel.WARNING, traceback.format_exc())
                            traceback.print_exc()

                    @cls.alpaca_stream.on(r'^status$')
                    async def on_status(conn, channel, msg):
                        try:
                            cls._on_status_update(msg.message, logfeed_data)
                        except Exception as e:
                            logfeed_data.log(LogLevel.ERROR, 'Error handling polygon status update:')
                            logfeed_data.log(LogLevel.WARNING, traceback.format_exc())
                            traceback.print_exc()

                    @cls.alpaca_stream.on(r'^A$')
                    async def on_second_bars(conn, channel, data):
                        # start_queue = pytime.monotonic()
                        try:
                            # print(str(data))
                            # print(f'is {data.start:%Y/%m/%d_%H:%M:%S}')
                            # print(f'at {datetime.now():%Y/%m/%d_%H:%M:%S}')
                            cls._on_data_update(data)
                        except Exception as e:
                            logfeed_data.log(LogLevel.ERROR, 'Error handling polygon candle update:')
                            logfeed_data.log(LogLevel.WARNING, traceback.format_exc())
                            traceback.print_exc()
                        # queue_time_ms = (pytime.monotonic() - start_queue) * 1000
                        # moment = datetime.strptime(data.start.strftime(DATE_TIME_FORMAT), DATE_TIME_FORMAT)
                        """
                        try:
                            if queue_time_ms > 80:
                                print(f'took {queue_time_ms:.0f}ms to queue {data.symbol} {moment:%M:%S} candle')
                            else:
                                print(f'queued {data.symbol} {moment:%M:%S} candle at {datetime.now():%M:%S}')
                        except Exception as e:
                            traceback.print_exc()
                        """

                    # Subscribe to alpaca and polygon streams
                    channels_to_stream = ['trade_updates', 'account_updates']
                    channels_to_stream.extend(f'A.{symbol}' for symbol in symbols)

                    logfeed_data.log(LogLevel.INFO, 'Subscribing to polygon and alpaca streams')
                    cls.alpaca_stream.run(channels_to_stream)
                except Exception as e:
                    logfeed_data.log(LogLevel.ERROR, 'Polygon and alpaca streams disconnected unexpectedly')
                    logfeed_data.log(LogLevel.WARNING, traceback.format_exc())
                    pytime.sleep(2)
                    logfeed_data.log(LogLevel.INFO, 'Attempting to re-connect data streams')

        # Connect to the streams in another thread
        cls.streams_thread = Thread(target=init_streams)
        cls.streams_thread.start()

    @classmethod
    def add_symbol(cls,
                   symbol: str) -> None:
        """Starts listening for data updates on the symbol, if not already listening."""
        cls.alpaca_stream.unsubscribe(f'A.{symbol}')
        cls.alpaca_stream.subscribe(f'A.{symbol}')

    @classmethod
    def remove_symbol(cls,
                      symbol: str) -> None:
        """Stops listening for data updates on the symbol."""
        cls.alpaca_stream.unsubscribe(f'A.{symbol}')

    @classmethod
    def shutdown(cls):
        """Unsubscribes to alpaca and polygon stream updates and closes the connection."""
        cls.running = False
        if cls.alpaca_stream is not None:
            async def close_task():
                await cls.alpaca_stream.close()

            asyncio.create_task(close_task)
        pytime.sleep(0.2)
        pytime.sleep(0.2)
        pytime.sleep(0.2)

    """
    Private methods...
    """

    @classmethod
    def _on_account_update(cls,
                           raw_msg,
                           logfeed_data: LogFeed) -> None:
        """
        Adds an update signal to the queues, which are processed by AbstractAccount's on other threads.
        """
        # Decode raw msg into json
        data = raw_msg.account

        # Check that the account is active
        if data['status'].lower() != 'active':
            logfeed_data.log(LogLevel.WARNING, 'Alpaca account status is "{0}"'.format(data['status']))
            logfeed_data.log(LogLevel.WARNING, 'Alpaca account status is "{0}"'.format(data['status']))

        # Convert account info json into an AccountInfo object
        acct_info = AccountInfo(data['id'], float(data['cash']), float(data['cash_withdrawable']))

        # Add the account update to the data queue
        cls._queue_update(moment=datetime.now(),
                          update_type=StreamUpdateType.ACCT_INFO,
                          acct_info=acct_info.to_json())

    @classmethod
    def _on_trade_update(cls,
                         order: Order) -> None:
        """
        Adds the updated order to the queues, which are processed by AbstractAccount's on other threads.
        """

        # Signal the running strategy to respond to this new order update
        cls._queue_update(moment=datetime.now(),
                          update_type=StreamUpdateType.ORDER,
                          symbol=order.symbol,
                          order=order.to_json())

    @classmethod
    def _on_data_update(cls,
                        data) -> None:
        """
        Adds the new candle to the queues, which are processed by AbstractAccount's on other threads.
        """

        # Get candle's symbol
        symbol = data.symbol

        # Get candle's pandas timestamp as a datetime
        moment = datetime.strptime(data.start.strftime(DATE_TIME_FORMAT), DATE_TIME_FORMAT)

        # Compile candle object
        candle = Candle(moment=moment,
                        open=data.open,
                        high=data.high,
                        low=data.low,
                        close=data.close,
                        volume=data.volume)

        # Signal the running strategy to respond to this new price data
        cls._queue_update(moment=moment,
                          update_type=StreamUpdateType.CANDLE,
                          symbol=symbol,
                          candle=candle.to_json())

    @classmethod
    def _on_status_update(cls,
                          event: str,
                          logfeed_data: LogFeed) -> None:
        """
        Logs messages received from alpaca.markets and polygon.io.
        """

        # Ignore uninteresting polygon status updates
        if event == 'Connecting to Polygon' or event == 'Connected Successfully':
            logfeed_data.log(LogLevel.DEBUG, event)
            try:
                cls._queue_update(moment=datetime.now(),
                                  update_type=StreamUpdateType.STARTED_UP)
            except Exception as e:
                logfeed_data.log(LogLevel.ERROR, 'Error queuing ws startup update:')
                logfeed_data.log(LogLevel.WARNING, traceback.format_exc())
                traceback.print_exc()

        # Log successful authentication with polygon websocket
        elif event == 'authenticated':
            logfeed_data.log(LogLevel.DEBUG,
                             'Successfully authenticated Polygon.io live stream (all channels unsubscribed)')

        # Log successful channel subscription messages
        elif event.startswith('subscribed to:'):
            logfeed_data.log(LogLevel.DEBUG,
                             'Subscribed to Polygon websocket channel: {0}'.format(event.split('to: ')[1]))

        # Log unrecognized polygon status updates
        else:
            logfeed_data.log(LogLevel.INFO, 'Unknown polygon.io status message: {0}'.format(event))

    @classmethod
    def _queue_update(cls,
                      moment: datetime,
                      update_type: StreamUpdateType,
                      acct_info: dict = None,
                      symbol: str = None,
                      candle: dict = None,
                      order: dict = None) -> None:
        """
        Adds an update to the stream's queue.
        """

        # Create a StreamUpdate object
        update = StreamUpdate(update_moment=moment,
                              update_type=update_type,
                              acct_info=acct_info,
                              symbol=symbol,
                              candle=candle,
                              order=order)

        # Add the update to the multi-threaded list
        cls._livestream_updates.append(update.to_json())

        # Prune the update queue
        if cls._queue_initially_filled.value and len(cls._livestream_updates) > 600:
            while len(cls._livestream_updates) > 500:
                cls._livestream_updates.pop(0)
        elif len(cls._livestream_updates) > 600:
            cls._queue_initially_filled.value = True
