import enum


class STATUS(enum.Enum):
    LOGGED = enum.auto()
    NOT_LOGGED = enum.auto()


class MODES(enum.Enum):
    BUY = 0
    SELL = 1


class PERIOD(enum.Enum):
    ONE_MINUTE = 1
    FIVE_MINUTES = 5
    FIFTEEN_MINUTES = 15
    THIRTY_MINUTES = 30
    ONE_HOUR = 60
    FOUR_HOURS = 240
    ONE_DAY = 1440
    ONE_WEEK = 10080
    ONE_MONTH = 43200


class TRANSACTION_TYPE(enum.Enum):
    OPEN = 0
    CLOSE = 2


class TRANSACTION_STATUS(enum.Enum):
    ERROR = 0
    PENDING = 1
    REQUOTED = 2
    ACCEPTED = 3
    REJECTED = 4
    PRICED = 5


class TRANSACTION:
    def __init__(
        self,
        order,
        symbol,
        close_price,
        profit,
        volume,
        sl,
        tp,
        *args,
        **kwargs,
    ):
        self.order = order
        self.symbol = symbol
        self.profit = profit
        self.volume = volume
        self.price = close_price
        self.sl = sl
        self.tp = tp
