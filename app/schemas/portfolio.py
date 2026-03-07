from typing import Optional

from pydantic import BaseModel, ConfigDict


class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
