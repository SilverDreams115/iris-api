from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SignalCreate(BaseModel):
    symbol: str
    side: str
    confidence: Decimal = Field(gt=0, le=100)
    status: str = "pending"
    source: str = "manual"
    notes: Optional[str] = None
    strategy_id: int
    trade_id: Optional[int] = None


class SignalUpdate(BaseModel):
    symbol: Optional[str] = None
    side: Optional[str] = None
    confidence: Optional[Decimal] = Field(default=None, gt=0, le=100)
    status: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    strategy_id: Optional[int] = None
    trade_id: Optional[int] = None


class SignalResponse(BaseModel):
    id: int
    symbol: str
    side: str
    confidence: Decimal
    status: str
    source: str
    notes: Optional[str]
    owner_id: int
    strategy_id: int
    trade_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)
