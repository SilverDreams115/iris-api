from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.enums import SignalSide, SignalSource, SignalStatus


class SignalCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=50)
    side: SignalSide
    confidence: Decimal = Field(gt=0, le=100)
    status: SignalStatus = SignalStatus.pending
    source: SignalSource = SignalSource.manual
    notes: Optional[str] = None
    strategy_id: int
    trade_id: Optional[int] = None
    rejection_reason: Optional[str] = Field(default=None, min_length=1, max_length=500)

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
    notes: Optional[str] = None
    trade_id: Optional[int] = None


class SignalRejectRequest(BaseModel):
    rejection_reason: str = Field(min_length=1, max_length=500)
    notes: Optional[str] = None


class SignalUpdate(BaseModel):
    symbol: Optional[str] = Field(default=None, min_length=1, max_length=50)
    side: Optional[SignalSide] = None
    confidence: Optional[Decimal] = Field(default=None, gt=0, le=100)
    status: Optional[SignalStatus] = None
    source: Optional[SignalSource] = None
    notes: Optional[str] = None
    strategy_id: Optional[int] = None
    trade_id: Optional[int] = None
    rejection_reason: Optional[str] = Field(default=None, min_length=1, max_length=500)

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
    notes: Optional[str]
    owner_id: int
    strategy_id: int
    trade_id: Optional[int]
    rejection_reason: Optional[str] = None
    executed_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
