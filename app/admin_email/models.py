# models.py

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class Role(str, Enum):
    admin = "Admin"
    super_admin = "Super Admin"
    user = "User"

class AdminBase(BaseModel):
    user_name: str = Field(..., example="john_doe")
    email: str = Field(..., example="john.doe@example.com")
    role: Role = Field(..., example=Role.admin)
    status: bool = Field(..., example=True)

class AdminCreate(AdminBase):
    pass

class AdminUpdate(BaseModel):
    user_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Role] = None
    status: Optional[bool] = None

class AdminInDB(AdminBase):
    id: str = Field(..., alias="_id")
