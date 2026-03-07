from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.enums import TradeSide, TradeStatus


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

    @model_validator(mode="after")
    def validate_closed_trade_payload(self):
        if self.status == TradeStatus.closed and self.exit_price is None:
            raise ValueError("Closed trades require exit_price")
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

    @model_validator(mode="after")
    def validate_update_payload(self):
        if self.status == TradeStatus.closed and self.exit_price is None:
            raise ValueError("Closed trades require exit_price")
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
