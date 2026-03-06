from typing import Optional

from pydantic import BaseModel, ConfigDict


class BrokerAccountCreate(BaseModel):
    broker_name: str
    account_label: str
    account_type: str


class BrokerAccountUpdate(BaseModel):
    broker_name: Optional[str] = None
    account_label: Optional[str] = None
    account_type: Optional[str] = None
    status: Optional[str] = None


class BrokerAccountResponse(BaseModel):
    id: int
    broker_name: str
    account_label: str
    account_type: str
    status: str
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
