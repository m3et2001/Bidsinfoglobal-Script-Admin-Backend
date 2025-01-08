from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DeveloperStatus(str, Enum):
    active = "Active"
    inactive = "Inactive"

class DeveloperBase(BaseModel):
    name: str = Field(..., example="John Doe")
    joining_date: datetime = Field(..., example=datetime.now())
    email: str = Field(..., example="john.doe@example.com")
    phone_number: str = Field(..., example="+1234567890")
    address: str = Field(..., example="1234 Elm St, Springfield")
    total_script_count: int = Field(..., example=10)
    active_script_count: int = Field(..., example=8)
    maintain_script_count: int = Field(..., example=2)
    status: DeveloperStatus = Field(..., example=DeveloperStatus.active)

class DeveloperCreate(DeveloperBase):
    pass

class DeveloperUpdate(BaseModel):
    name: Optional[str] = None
    joining_date: Optional[datetime] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    total_script_count: Optional[int] = None
    active_script_count: Optional[int] = None
    maintain_script_count: Optional[int] = None
    status: Optional[DeveloperStatus] = None

class DeveloperInDB(DeveloperBase):
    id: str = Field(..., alias="_id")
