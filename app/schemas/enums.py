from enum import Enum


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class TradeSide(str, Enum):
    buy = "buy"
    sell = "sell"


class TradeStatus(str, Enum):
    open = "open"
    closed = "closed"
    cancelled = "cancelled"


class BrokerAccountType(str, Enum):
    demo = "demo"
    live = "live"


class BrokerAccountStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class StrategyTimeframe(str, Enum):
    m1 = "M1"
    m5 = "M5"
    m15 = "M15"
    m30 = "M30"
    h1 = "H1"
    h4 = "H4"
    d1 = "D1"


class SignalSide(str, Enum):
    buy = "buy"
    sell = "sell"


class SignalStatus(str, Enum):
    pending = "pending"
    executed = "executed"
    rejected = "rejected"
    cancelled = "cancelled"


class SignalSource(str, Enum):
    manual = "manual"
    strategy = "strategy"
    external = "external"
