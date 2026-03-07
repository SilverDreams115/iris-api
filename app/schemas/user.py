from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=255)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
