from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class RoleEnum(str, Enum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }


class UserRead(UserBase):
    id: int
    role: RoleEnum

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = {
        "populate_by_name": True,
        "from_attributes": False,
    }


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[RoleEnum] = None

    model_config = {
        "populate_by_name": True,
        "from_attributes": False,
    }
