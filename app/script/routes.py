from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException, status,File,Query
from typing import List
from db import get_database
from .crud import create_script, get_script, update_script, delete_script, list_scripts,get_scripts_by_developer,get_all_scheduled_scripts,LOGS_FOLDER,SCRIPTS_COLLECTION,get_script_type,get_frequencies,add_big_refs_to_script
from .models import ScriptCreate, ScriptUpdate, ScriptInDB,ScriptType,ScheduledScript,ScheduledScriptInDB,Frequency,AddBigRefData
from .validators import validate_data
from datetime import date,time,datetime
from fastapi.responses import JSONResponse

from typing import Optional
from utils.utils import get_current_user
import os
from .scheduler import get_scheduler
from fastapi.responses import FileResponse
from dotenv import load_dotenv
load_dotenv() 

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

@router.get("/frequencies", response_description="List all frequencies", response_model=List[str])
def get_frequencie_list(user: str = Depends(get_current_user)):
    return get_frequencies()

@router.get("/script-type")
def get_script_type_list(user: str = Depends(get_current_user)):
    return get_script_type()

@router.post("/add-big-refs")
def add_big_refs(data:AddBigRefData,db=Depends(get_database),user: str = Depends(get_current_user)):
    # print("sdfsdf",data.scrap_count)
    return add_big_refs_to_script(db,data)

@router.get("/scheduled-scripts", response_model=List[ScheduledScriptInDB])
def api_get_all_scheduled_scripts(db=Depends(get_database),
                                    page: int = Query(1, ge=1, description="The page number to retrieve (1-based index)"),
                                    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (max 100)"),
                                    user: str = Depends(get_current_user)):
    jobs = get_scheduler().get_jobs()
    print(jobs)
    
    return get_all_scheduled_scripts(db,page_size,page)


@router.post("", response_description="Create a new script", response_model=ScriptInDB, status_code=status.HTTP_201_CREATED)
def create_script_endpoint(
    db=Depends(get_database),
    script_name: str = Form(...),
    developer_id: str = Form(...),
    development_date: str = Form("2024-02-02", example="2024-02-02"),  # Use string for date input
    schedule_time: str = Form("09:23", example="09:23"), 
    country: str = Form(...),
    script_status: bool = Form(...),
    bigref_no: list = Form(...),
    recent_logs: str = Form(None),
    script_type: ScriptType = Form(...),
    frequency: Frequency = Form(...),
    interval_days: Optional[int] = Form(None),
    file: UploadFile = File(...),
    user: str = Depends(get_current_user)

):

    validate_data(
    file=file,
    development_date=development_date,
    developer_id=developer_id,
    bigref_no=bigref_no,
    schedule_time=schedule_time,
    interval_days=interval_days

)
    script_data = ScriptCreate(
        script_name=script_name,
        developer_id=developer_id,
        development_date= development_date,
        schedule_time=datetime.strptime(schedule_time, "%H:%M"),
        country=country,
        status=script_status,
        bigref_no=bigref_no,
        frequency=frequency,
        interval_days=interval_days,
        script_type=script_type,
        recent_logs=recent_logs
    )
    new_script = create_script(db, script_data, file)
    return new_script

@router.get("/{script_id}", response_description="Get a script by ID", response_model=ScriptInDB)
def get_script_endpoint(script_id: str, db=Depends(get_database),user: str = Depends(get_current_user)):
    script = get_script(db, script_id)
    if script is None:
        return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": "error",
                    "message": "Script not found",
                    "data": None,
                },
            )
    return script

@router.put("/{script_id}", response_description="Update a script", response_model=ScriptInDB)
def update_script_endpoint(
  script_id: str,
    db=Depends(get_database),
    script_name: Optional[str] = Form(None),
    developer_id: Optional[str] = Form(None),
    development_date: Optional[str] = Form("2024-02-02", example="2024-02-02"),  # Use string for date input
    schedule_time: Optional[str] = Form("09:23", example="09:23"), 
    country: Optional[str] = Form(None),
    script_status: Optional[bool] = Form(None),
    # bigref_no: Optional[list] = Form(None),
    # recent_logs: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    script_type: ScriptType = Form(...),
    frequency: Frequency = Form(...),
    interval_days: Optional[int] = Form(None),
    user: str = Depends(get_current_user)
    ):
    validate_data(
    file=file,
    development_date=development_date,
    developer_id=developer_id,
    # bigref_no=bigref_no,
    schedule_time=schedule_time,
    interval_days=interval_days
)
    script_update = ScriptUpdate(
        script_name=script_name,
        developer_id=developer_id,
        development_date= development_date,
        schedule_time=datetime.strptime(schedule_time, "%H:%M"),
        country=country,
        status=script_status,
        # bigref_no=bigref_no,
        frequency=frequency,
        interval_days=interval_days,
        script_type=script_type,
        # recent_logs=recent_logs
    )
    
    updated_script = update_script(db, script_id, script_update,file)
    if updated_script is None:
        return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": "error",
                    "message": "Script not found",
                    "data": None,
                },
            )
        
    return updated_script

@router.delete("/{script_id}", response_description="Delete a script")
def delete_script_endpoint(script_id: str, db=Depends(get_database),user: str = Depends(get_current_user)):
    deleted = delete_script(db, script_id)
    if not deleted:
        return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": "error",
                    "message": "Script not found",
                    "data": None,
                },
            )
    return deleted

@router.get("", response_description="List all scripts", response_model=List[ScriptInDB])
def list_scripts_endpoint(db=Depends(get_database),
                            pageNo: int = Query(1, ge=1, description="The page number to retrieve (1-based index)"),
                            limit: int = Query(10, ge=1, le=100, description="Number of items per page (max 100)"),
                            user: str = Depends(get_current_user)):
    scripts = list_scripts(db, limit,pageNo)
    return scripts

@router.get("/developer/{developer_id}", response_description="Get all scripts by developer", response_model=List[ScriptInDB])
def get_all_scripts_by_developer(developer_id: str, db=Depends(get_database),
                                pageNo: int = Query(1, ge=1, description="The page number to retrieve (1-based index)"),
                                limit: int = Query(10, ge=1, le=100, description="Number of items per page (max 100)"),
                                user: str = Depends(get_current_user)):
    scripts = get_scripts_by_developer(db, developer_id,limit,pageNo)
    return scripts




@router.get("/download-log/{filename}")
def download_log(filename: str, user: str = Depends(get_current_user)):
    file_path = os.path.join(LOGS_FOLDER, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/octet-stream", filename=filename)
    return JSONResponse(
        status_code=404,
        content={"status": "error", "message": "Log file not found."},
    )

@router.put("/update-script-status/:script_name")
async def update_script_status( script_name:str,db=Depends(get_database), user: str = Depends(get_current_user)):
    """
    Update the status of a script by matching its name.
    """
    try:
        # Find the script by name and update its status
        result = db[SCRIPTS_COLLECTION].update_one({"script_name":script_name},{"$set": {"status": "false"}})
        

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Script with the given name not found."
            )

        return {
            "status": "success",
            "message": "Script status updated successfully.",
            "updated_count": result.modified_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {e}"
        )
    
