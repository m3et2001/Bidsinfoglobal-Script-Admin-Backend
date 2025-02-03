from pydantic import BaseModel, Field
from typing import Optional,List, Dict, Union
from datetime import datetime,date,time
from enum import Enum

class ScriptType(str, Enum):
    tender = "Tender"
    project = "Project"
    grant = "Grant"
    contract_award = "Contract Award"

class Frequency(str, Enum):
    one_time = "One Time"
    daily = "Daily"
    weekly = "Weekly"
    monthly = "Monthly"
    custom = "Custom"  # Allows user to specify a custom interval


# Define the request body model
class AddBigRefData(BaseModel):
    big_ref_no: List[str]  # List of big_ref_no
    script_name: str  # Name of the script
    scrap_count: str  # Developer identifier


class ScriptBase(BaseModel):
    script_name: str = Field(..., example="DataProcessor")
    developer_id: str = Field(..., example="Jane Doe")
    development_date: datetime = Field(..., example=datetime.now().date())
    schedule_time: datetime = Field(..., example="03:70")
    country: str = Field(..., example="USA")
    status: bool = Field(..., example="true")
    bigref_no: list = Field(..., example=["BR123456"])
    recent_logs: Optional[str] = Field(None, example="Initial commit")
    script_file_path: Optional[str] = Field(None, example="uploaded_scripts/script.py")
    script_type: ScriptType = Field(..., example=ScriptType.tender)
    # Frequency field (predefined options or custom interval)
    frequency: Frequency = Field(..., example=Frequency.daily)
    # If frequency is "custom", user can specify an interval in days
    interval_days: Optional[int] = Field(None, example=2, description="Interval in days if frequency is 'custom'")
    scraped_data: List[Dict[str, Union[str, int]]] = Field(
        default=[], 
        example=[
            {"date": "2025-02-01", "scraped_count": 10,"bigref_no":[]},
            {"date": "2025-02-02", "scraped_count": 15,"bigref_no":[]}
        ],
        description="List of dates and the number of tenders scraped on each date."
    )

    

class ScriptCreate(ScriptBase):
    pass

class ScriptUpdate(BaseModel):
    script_name: Optional[str] = None
    developer_id: Optional[str] = None
    development_date: Optional[datetime] = None
    schedule_time: datetime = Field(..., example=datetime.now().time())
    country: Optional[str] = None
    status: Optional[bool] = None
    bigref_no: Optional[list] = None
    recent_logs: Optional[str] = None
    script_file_path: Optional[str] = None
    script_type: Optional[ScriptType] = None
    frequency: Optional[Frequency] = None
    # If frequency is "custom", user can specify an interval in days
    interval_days: Optional[int] = Field(None, example=2, description="Interval in days if frequency is 'custom'")

class ScriptInDB(ScriptBase):
    id: str = Field(..., alias="_id")

class ScheduledScript(BaseModel):
    script_name: str
    schedule_time: str

class ScheduledScriptInDB(BaseModel):
    script_name: str
    schedule_time: str
    script_file_path: str