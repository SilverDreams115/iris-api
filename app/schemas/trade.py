from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.enums import TradeSide, TradeStatus


class TradeCreate(BaseModel):
    symbol: str
    side: TradeSide
    volume: Decimal = Field(gt=0)
    entry_price: Decimal = Field(gt=0)
    exit_price: Optional[Decimal] = Field(default=None, gt=0)
    stop_loss: Optional[Decimal] = Field(default=None, gt=0)
    take_profit: Optional[Decimal] = Field(default=None, gt=0)
    status: TradeStatus = TradeStatus.open
    pnl: Optional[Decimal] = None
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
    symbol: Optional[str] = None
    side: Optional[TradeSide] = None
    volume: Optional[Decimal] = Field(default=None, gt=0)
    entry_price: Optional[Decimal] = Field(default=None, gt=0)
    exit_price: Optional[Decimal] = Field(default=None, gt=0)
    stop_loss: Optional[Decimal] = Field(default=None, gt=0)
    take_profit: Optional[Decimal] = Field(default=None, gt=0)
    status: Optional[TradeStatus] = None
    pnl: Optional[Decimal] = None
    strategy_id: Optional[int] = None
    broker_account_id: Optional[int] = None

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
    exit_price: Optional[Decimal]
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    status: TradeStatus
    pnl: Optional[Decimal]
    closed_at: Optional[datetime]
    owner_id: int
    strategy_id: int
    broker_account_id: int

    model_config = ConfigDict(from_attributes=True)
