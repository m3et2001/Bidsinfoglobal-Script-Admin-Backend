from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException, status,File
from typing import List
from db import get_database
from .crud import create_script, get_script, update_script, delete_script, list_scripts,get_scripts_by_developer
from .models import ScriptCreate, ScriptUpdate, ScriptInDB,ScriptType

from datetime import date
import datetime
from fastapi import HTTPException
from typing import Optional
from utils.utils import get_current_user

ALLOWED_EXTENSIONS = {'.py'}
ALLOWED_MIME_TYPES = {'text/x-python'}

def validate_file(file: UploadFile):
    filename = file.filename
    mime_type = file.content_type

    # Check file extension
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check MIME type
    # if mime_type not in ALLOWED_MIME_TYPES:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Invalid MIME type. Allowed MIME types are: {', '.join(ALLOWED_MIME_TYPES)}",
    #     )



router = APIRouter()

@router.post("/", response_description="Create a new script", response_model=ScriptInDB, status_code=status.HTTP_201_CREATED)
def create_script_endpoint(
    db=Depends(get_database),
    script_name: str = Form(...),
    developer_id: str = Form(...),
    development_date: date = Form(...),
    country: str = Form(...),
    status: bool = Form(...),
    bigref_no: list = Form(...),
    recent_logs: str = Form(None),
    script_type: ScriptType = Form(...),
    file: UploadFile = File(...),
    user: str = Depends(get_current_user)

):
    validate_file(file)
    script_data = ScriptCreate(
        script_name=script_name,
        developer_id=developer_id,
        development_date= development_date,
        country=country,
        status=status,
        bigref_no=bigref_no,
        script_type=script_type,
        recent_logs=recent_logs
    )
    new_script = create_script(db, script_data, file)
    return new_script

@router.get("/{script_id}", response_description="Get a script by ID", response_model=ScriptInDB)
def get_script_endpoint(script_id: str, db=Depends(get_database),user: str = Depends(get_current_user)):
    script = get_script(db, script_id)
    if script is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")
    return script

@router.put("/{script_id}", response_description="Update a script", response_model=ScriptInDB)
def update_script_endpoint(
  script_id: str,
    db=Depends(get_database),
    script_name: Optional[str] = Form(None),
    developer_id: Optional[str] = Form(None),
    development_date: Optional[date] = Form(None),
    country: Optional[str] = Form(None),
    script_status: Optional[bool] = Form(None),
    bigref_no: Optional[list] = Form(None),
    recent_logs: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    script_type: ScriptType = Form(...),
    user: str = Depends(get_current_user)
    ):
    script_update = ScriptUpdate(
        script_name=script_name,
        developer_id=developer_id,
        development_date=development_date,
        country=country,
        status=script_status,
        bigref_no=bigref_no,
        script_type=script_type,
        recent_logs=recent_logs
    )
    if(file):
        validate_file(file)
    updated_script = update_script(db, script_id, script_update,file)
    if updated_script is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found or no changes made")
    return updated_script

@router.delete("/{script_id}", response_description="Delete a script")
def delete_script_endpoint(script_id: str, db=Depends(get_database),user: str = Depends(get_current_user)):
    deleted = delete_script(db, script_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")
    return {"message": "Script deleted successfully"}

@router.get("/", response_description="List all scripts", response_model=List[ScriptInDB])
def list_scripts_endpoint(db=Depends(get_database),user: str = Depends(get_current_user), limit: int = 100):
    scripts = list_scripts(db, limit)
    return scripts

@router.get("/scripts/{developer_id}", response_description="Get all scripts by developer", response_model=List[ScriptInDB])
def get_all_scripts_by_developer(developer_id: str, db=Depends(get_database)):
    scripts = get_scripts_by_developer(db, developer_id)
    return scripts