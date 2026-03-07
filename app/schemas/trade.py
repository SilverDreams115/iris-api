from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.enums import TradeSide, TradeStatus


def _validate_price_relationship(
    side: TradeSide | None,
    entry_price: Decimal | None,
    stop_loss: Decimal | None,
    take_profit: Decimal | None,
) -> None:
    if side is None or entry_price is None or stop_loss is None or take_profit is None:
        return

    if side == TradeSide.buy:
        if not (stop_loss < entry_price < take_profit):
            raise ValueError("Invalid price relationship for buy trade")

    elif side == TradeSide.sell:
        if not (take_profit < entry_price < stop_loss):
            raise ValueError("Invalid price relationship for sell trade")


class TradeCreate(BaseModel):
    symbol: str
    side: TradeSide
    volume: Decimal = Field(gt=0)
    entry_price: Decimal = Field(gt=0)
    exit_price: Decimal | None = Field(default=None, gt=0)
    stop_loss: Decimal | None = Field(default=None, gt=0)
    take_profit: Decimal | None = Field(default=None, gt=0)
    status: TradeStatus = TradeStatus.open
    pnl: Decimal | None = None
    strategy_id: int
    broker_account_id: int

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("Trade symbol cannot be empty")
        return value

    @model_validator(mode="after")
    def validate_closed_trade_payload(self):
        if self.status == TradeStatus.closed and self.exit_price is None:
            raise ValueError("Closed trades require exit_price")

        _validate_price_relationship(
            self.side,
            self.entry_price,
            self.stop_loss,
            self.take_profit,
        )
        return self


class TradeCloseRequest(BaseModel):
    exit_price: Decimal = Field(gt=0)
    pnl: Decimal


class TradeUpdate(BaseModel):
    symbol: str | None = None
    side: TradeSide | None = None
    volume: Decimal | None = Field(default=None, gt=0)
    entry_price: Decimal | None = Field(default=None, gt=0)
    exit_price: Decimal | None = Field(default=None, gt=0)
    stop_loss: Decimal | None = Field(default=None, gt=0)
    take_profit: Decimal | None = Field(default=None, gt=0)
    status: TradeStatus | None = None
    pnl: Decimal | None = None
    strategy_id: int | None = None
    broker_account_id: int | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().upper()
        if not value:
            raise ValueError("Trade symbol cannot be empty")
        return value

    @model_validator(mode="after")
    def validate_update_payload(self):
        if self.status == TradeStatus.closed and self.exit_price is None:
            raise ValueError("Closed trades require exit_price")

        _validate_price_relationship(
            self.side,
            self.entry_price,
            self.stop_loss,
            self.take_profit,
        )
        return self


class TradeResponse(BaseModel):
    id: int
    symbol: str
    side: TradeSide
    volume: Decimal
    entry_price: Decimal
    exit_price: Decimal | None
    stop_loss: Decimal | None
    take_profit: Decimal | None
    status: TradeStatus
    pnl: Decimal | None
    closed_at: datetime | None
    owner_id: int
    strategy_id: int
    broker_account_id: int

    model_config = ConfigDict(from_attributes=True)
