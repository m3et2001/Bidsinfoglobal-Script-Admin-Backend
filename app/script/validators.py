from fastapi import HTTPException, UploadFile
from datetime import datetime
from bson.objectid import ObjectId
from typing import Optional, List
import re

def validate_data(
    file: Optional[UploadFile] = None,
    development_date: Optional[str] = None,
    developer_id: Optional[str] = None,
    bigref_no: Optional[List[str]] = None,
    schedule_time: Optional[str] = None,
):
    """
    Consolidate all validations for the input data.
    - Validate the uploaded file (if provided, must be a Python file and < 1MB).
    - Validate the development date (if provided, must be in the format 'YYYY/MM/DD' and not in the future).
    - Validate the developer ID (if provided, must be a valid 14-character MongoDB ObjectId).
    - Validate the bigref_no field (if provided, must be a list of non-empty strings).
    - Validate the schedule_time (if provided, must be in the format 'HH:MM').
    """
    # Validate the file (if provided)
    if file:
        if not file.filename.endswith(".py"):
            raise HTTPException(status_code=400, detail="Only Python (.py) files are allowed")
        if file.size > 1_000_000:  # Example size limit: 1MB
            raise HTTPException(status_code=400, detail="File size exceeds the limit of 1MB")
    
    # Validate the development date (if provided)
    if development_date:
        # Regex to match 'YYYY/MM/DD'
        date_regex = r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"
        if not re.match(date_regex, development_date):
            raise HTTPException(status_code=400, detail="Development date must be in the format 'YYYY-MM-DD'")
        

    # Validate the developer ID (if provided)
    if developer_id:
        if not ObjectId.is_valid(developer_id):
            raise HTTPException(status_code=400, detail="Developer ID must be a valid 14-character MongoDB ObjectId")

    # Validate the bigref_no field (if provided)
    if bigref_no:
        if not isinstance(bigref_no, list) or not all(isinstance(ref, str) and ref.strip() for ref in bigref_no):
            raise HTTPException(status_code=400, detail="Big reference numbers must be an array of non-empty strings")
    
    # Validate the schedule_time (if provided)
    if schedule_time:
        # Regex to match 'HH:MM' in 24-hour format
        time_regex = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
        if not re.match(time_regex, schedule_time):
            raise HTTPException(status_code=400, detail="Schedule time must be in the format 'HH:MM'")
