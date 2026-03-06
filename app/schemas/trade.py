from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TradeCreate(BaseModel):
    symbol: str
    side: str
    volume: Decimal = Field(gt=0)
    entry_price: Decimal = Field(gt=0)
    exit_price: Optional[Decimal] = Field(default=None, gt=0)
    stop_loss: Optional[Decimal] = Field(default=None, gt=0)
    take_profit: Optional[Decimal] = Field(default=None, gt=0)
    status: str = "open"
    pnl: Optional[Decimal] = None
    strategy_id: int
    broker_account_id: int


class TradeUpdate(BaseModel):
    symbol: Optional[str] = None
    side: Optional[str] = None
    volume: Optional[Decimal] = Field(default=None, gt=0)
    entry_price: Optional[Decimal] = Field(default=None, gt=0)
    exit_price: Optional[Decimal] = Field(default=None, gt=0)
    stop_loss: Optional[Decimal] = Field(default=None, gt=0)
    take_profit: Optional[Decimal] = Field(default=None, gt=0)
    status: Optional[str] = None
    pnl: Optional[Decimal] = None
    strategy_id: Optional[int] = None
    broker_account_id: Optional[int] = None


class TradeResponse(BaseModel):
    id: int
    symbol: str
    side: str
    volume: Decimal
    entry_price: Decimal
    exit_price: Optional[Decimal]
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    status: str
    pnl: Optional[Decimal]
    owner_id: int
    strategy_id: int
    broker_account_id: int

    model_config = ConfigDict(from_attributes=True)
