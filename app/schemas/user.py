from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)