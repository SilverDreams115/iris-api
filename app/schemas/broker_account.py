from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import BrokerAccountStatus, BrokerAccountType


class BrokerAccountCreate(BaseModel):
    broker_name: str = Field(min_length=1, max_length=255)
    account_label: str = Field(min_length=1, max_length=255)
    account_type: BrokerAccountType

    @field_validator("broker_name", "account_label")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value


class BrokerAccountUpdate(BaseModel):
    broker_name: str | None = Field(default=None, min_length=1, max_length=255)
    account_label: str | None = Field(default=None, min_length=1, max_length=255)
    account_type: BrokerAccountType | None = None
    status: BrokerAccountStatus | None = None

    @field_validator("broker_name", "account_label")
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value


class BrokerAccountResponse(BaseModel):
    id: int
    broker_name: str
    account_label: str
    account_type: BrokerAccountType
    status: BrokerAccountStatus
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
