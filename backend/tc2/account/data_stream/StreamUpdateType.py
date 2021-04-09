from enum import Enum


class StreamUpdateType(Enum):
    """
    Contains all the types of updates the AccountDataStream can emit.
    """

    # New serialized AccountInfo object, likely containing an updated balance
    ACCT_INFO = 'acct_info'

    # New candle containing a new second's worth of data
    CANDLE = 'candle'

    # New serialized Order object
    ORDER = 'order'

    # Signal that live data streaming just began
    # TODO This needs to get triggered whenever the data stream resets
    # TODO We need to respond by fetching latest positions from REST
    STARTED_UP = 'started_up'
