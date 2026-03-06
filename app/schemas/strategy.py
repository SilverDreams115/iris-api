from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import StrategyTimeframe


class StrategyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    symbol: str = Field(min_length=1, max_length=50)
    timeframe: StrategyTimeframe
    risk_percent: Decimal = Field(gt=0, le=100)
    portfolio_id: int
    broker_account_id: int


class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    symbol: Optional[str] = Field(default=None, min_length=1, max_length=50)
    timeframe: Optional[StrategyTimeframe] = None
    risk_percent: Optional[Decimal] = Field(default=None, gt=0, le=100)
    is_active: Optional[bool] = None
    portfolio_id: Optional[int] = None
    broker_account_id: Optional[int] = None


class StrategyResponse(BaseModel):
    id: int
    name: str
    symbol: str
    timeframe: StrategyTimeframe
    risk_percent: Decimal
    is_active: bool
    owner_id: int
    portfolio_id: int
    broker_account_id: int

    model_config = ConfigDict(from_attributes=True)
