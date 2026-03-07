from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.enums import SignalSide, SignalSource, SignalStatus


class SignalCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=50)
    side: SignalSide
    confidence: Decimal = Field(gt=0, le=100)
    status: SignalStatus = SignalStatus.pending
    source: SignalSource = SignalSource.manual
    notes: str | None = None
    strategy_id: int
    trade_id: int | None = None
    rejection_reason: str | None = Field(default=None, min_length=1, max_length=500)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("Signal symbol cannot be empty")
        return value

    @field_validator("notes", "rejection_reason")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_create_payload(self):
        if (
            self.status in {SignalStatus.rejected, SignalStatus.cancelled}
            and not self.rejection_reason
        ):
            raise ValueError("Rejected or cancelled signals require rejection_reason")
        return self


class SignalExecuteRequest(BaseModel):
    volume: Decimal = Field(gt=0)
    entry_price: Decimal = Field(gt=0)
    stop_loss: Decimal = Field(gt=0)
    take_profit: Decimal = Field(gt=0)
    notes: str | None = None
    trade_id: int | None = None

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value or None


class SignalRejectRequest(BaseModel):
    rejection_reason: str = Field(min_length=1, max_length=500)
    notes: str | None = None

    @field_validator("rejection_reason")
    @classmethod
    def normalize_rejection_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Rejection reason cannot be empty")
        return value

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value or None


class SignalUpdate(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=50)
    side: SignalSide | None = None
    confidence: Decimal | None = Field(default=None, gt=0, le=100)
    status: SignalStatus | None = None
    source: SignalSource | None = None
    notes: str | None = None
    strategy_id: int | None = None
    trade_id: int | None = None
    rejection_reason: str | None = Field(default=None, min_length=1, max_length=500)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().upper()
        if not value:
            raise ValueError("Signal symbol cannot be empty")
        return value

    @field_validator("notes", "rejection_reason")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_update_payload(self):
        if (
            self.status in {SignalStatus.rejected, SignalStatus.cancelled}
            and not self.rejection_reason
        ):
            raise ValueError("Rejected or cancelled signals require rejection_reason")
        return self


class SignalResponse(BaseModel):
    id: int
    symbol: str
    side: SignalSide
    confidence: Decimal
    status: SignalStatus
    source: SignalSource
    notes: str | None
    owner_id: int
    strategy_id: int
    trade_id: int | None
    rejection_reason: str | None = None
    executed_at: datetime | None = None
    rejected_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
