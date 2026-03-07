from pydantic import BaseModel, ConfigDict


class PortfolioCreate(BaseModel):
    name: str
    description: str | None = None


class PortfolioUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
