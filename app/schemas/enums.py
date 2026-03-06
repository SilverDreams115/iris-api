from enum import Enum


class TradeSide(str, Enum):
    buy = "buy"
    sell = "sell"


class TradeStatus(str, Enum):
    open = "open"
    closed = "closed"
    cancelled = "cancelled"
