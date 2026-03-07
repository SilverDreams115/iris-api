from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import StrategyTimeframe


class StrategyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    symbol: str = Field(min_length=1, max_length=50)
    timeframe: StrategyTimeframe
    risk_percent: Decimal = Field(gt=0, le=100)
    portfolio_id: int
    broker_account_id: int

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Strategy name cannot be empty")
        return value

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("Strategy symbol cannot be empty")
        return value


class StrategyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    symbol: str | None = Field(default=None, min_length=1, max_length=50)
    timeframe: StrategyTimeframe | None = None
    risk_percent: Decimal | None = Field(default=None, gt=0, le=100)
    is_active: bool | None = None
    portfolio_id: int | None = None
    broker_account_id: int | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Strategy name cannot be empty")
        return value

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().upper()
        if not value:
            raise ValueError("Strategy symbol cannot be empty")
        return value


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
