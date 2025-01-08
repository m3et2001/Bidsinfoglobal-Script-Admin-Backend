from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime,date
from enum import Enum

class ScriptType(str, Enum):
    tender = "Tender"
    project = "Project"
    grant = "Grant"
    contract_award = "Contract Award"
    other = "Other"
class ScriptBase(BaseModel):
    script_name: str = Field(..., example="DataProcessor")
    developer_id: str = Field(..., example="Jane Doe")
    development_date: datetime = Field(..., example=datetime.now())
    country: str = Field(..., example="USA")
    status: bool = Field(..., example="Active")
    bigref_no: list = Field(..., example=["BR123456"])
    recent_logs: Optional[str] = Field(None, example="Initial commit")
    script_file_path: Optional[str] = Field(None, example="uploaded_scripts/script.py")
    script_type: ScriptType = Field(..., example=ScriptType.tender)

class ScriptCreate(ScriptBase):
    pass

class ScriptUpdate(BaseModel):
    script_name: Optional[str] = None
    developer_id: Optional[str] = None
    development_date: Optional[datetime] = None
    country: Optional[str] = None
    status: Optional[bool] = None
    bigref_no: Optional[list] = None
    recent_logs: Optional[str] = None
    script_file_path: Optional[str] = None
    script_type: Optional[ScriptType] = None

class ScriptInDB(ScriptBase):
    id: str = Field(..., alias="_id")
