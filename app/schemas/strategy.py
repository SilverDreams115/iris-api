from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StrategyCreate(BaseModel):
    name: str
    symbol: str
    timeframe: str
    risk_percent: Decimal = Field(gt=0, le=100)
    portfolio_id: int
    broker_account_id: int


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    risk_percent: Optional[Decimal] = Field(default=None, gt=0, le=100)
    is_active: Optional[bool] = None
    portfolio_id: Optional[int] = None
    broker_account_id: Optional[int] = None


class StrategyResponse(BaseModel):
    id: int
    name: str
    symbol: str
    timeframe: str
    risk_percent: Decimal
    is_active: bool
    owner_id: int
    portfolio_id: int
    broker_account_id: int

    model_config = ConfigDict(from_attributes=True)
