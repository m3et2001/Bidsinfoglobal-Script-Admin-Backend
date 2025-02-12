from typing import List, Optional
from bson import ObjectId
from pymongo.database import Database
from .models import ScriptCreate, ScriptUpdate, ScriptInDB, ScheduledScript, ScheduledScriptInDB,Frequency,ScriptType
from fastapi import UploadFile, HTTPException, status
import os
from ..developer.crud import DEVELOPERS_COLLECTION
from .scheduler import schedule_script, SCRIPTS_SCHEDULE_COLLECTION,remove_schedule_script
from datetime import datetime
from fastapi.responses import JSONResponse
from dotenv import load_dotenv, dotenv_values
config = dotenv_values(".env")
load_dotenv() 

SCRIPTS_COLLECTION = "scripts"
UPLOAD_DIRECTORY_BASE = os.getenv("UPLOAD_DIRECTORY_BASE", "uploaded_scripts/")
LOGS_FOLDER = config["LOG_PATH"]

# UPLOAD_DIRECTORY_BASE = "/var/lib/jenkins/workspace/scripts/"
# UPLOAD_DIRECTORY_BASE = "uploaded_scripts/"

# Serialize datetime to ISO format string for JSON compatibility
def serialize_datetime(data):
    if isinstance(data, datetime):
        return data.isoformat()  # Convert datetime to ISO format
    if isinstance(data, dict):
        return {key: serialize_datetime(value) for key, value in data.items()}
    if isinstance(data, list):
        return [serialize_datetime(item) for item in data]
    return data

def save_file(file: UploadFile, file_name: str,script_type:str) -> str:
    try:
        UPLOAD_DIRECTORY=UPLOAD_DIRECTORY_BASE+script_type
        
        if not os.path.exists(UPLOAD_DIRECTORY):
            os.makedirs(UPLOAD_DIRECTORY)
    
        file_path = os.path.join(UPLOAD_DIRECTORY, file_name)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)  # Remove the old file
            print(f"[INFO] Removed old file: {file_path}")
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        return file_path
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error saving file: {e}")

def delete_file(file_path: str) -> bool:
    """Deletes a file from the system if it exists."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[INFO] Deleted file: {file_path}")
            return True
        else:
            print(f"[WARNING] File not found: {file_path}")
            return False
    except Exception as e:
        print(f"[ERROR] Error deleting file: {file_path}. Error: {e}")
        return False


def create_script(db: Database, script: ScriptCreate, file: UploadFile) -> JSONResponse:
    try:
        print("****************************start create script *******************************")
        print(f"[INFO] Validating developer ID: {script.developer_id}")
        # Validate developer
        developer = db[DEVELOPERS_COLLECTION].find_one({"_id": ObjectId(script.developer_id)})
        if not developer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer not found")
        
        print(f"[INFO] Checking for unique script name: {script.script_name}")
        # Check for unique script name
        existing_script = db[SCRIPTS_COLLECTION].find_one({"script_name": script.script_name})
        if existing_script:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Script with name '{script.script_name}' already exists.")
        
        # Save the file with the script name
        file_extension = file.filename.split(".")[-1]
        saved_file_name = f"{script.script_name}.{file_extension}"
        file_path = save_file(file, saved_file_name,script.script_type)

        # Prepare script dictionary for database insertion
        script_dict = script.dict()
        script_dict["script_file_path"] = file_path
        result = db[SCRIPTS_COLLECTION].insert_one(script_dict)
        script_dict["_id"] = str(result.inserted_id)
        print("[INFO] Script created successfully in the database.")

        # Schedule the script
        try:
            schedule_script(db, str(result.inserted_id), script_dict["script_name"], file_path, script_dict["schedule_time"],script_dict["frequency"],script_dict["interval_days"])
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        # Ensure that datetime fields are serialized
        serialized_data = serialize_datetime(script_dict)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "message": "Script created successfully.",
                "data":serialized_data,
            },
        )
    except HTTPException as http_exc:
        return JSONResponse(
            status_code=http_exc.status_code,
            content={
                "status": "error",
                "message": http_exc.detail,
                "data": None,
            },
        )
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error creating script: {e}",
                "data": None,
            },
        )
    
def get_recent_log_file(script_name: str):
    try:
        print(f"Looking for logs in folder: {LOGS_FOLDER} for script: {script_name}")
        
        # Filter files with the script_name prefix
        matching_files = []
        for file in os.listdir(LOGS_FOLDER):
            if file.startswith(f"{script_name}_") and file.endswith(".log"):
                print(f"Found log file: {file}")
                timestamp_str = file[len(script_name) + 1 : -4]  # Extract the timestamp
                try:
                    # Parse the timestamp to validate
                    datetime.strptime(timestamp_str, "%Y-%m-%d-%H-%M-%S")
                    matching_files.append(file)  # Append only the file name, not the full path
                except ValueError:
                    print(f"Skipping invalid log file: {file}")
                    continue

        if not matching_files:
            print("No matching log files found.")
            return None

        # Sort by timestamp and get the most recent file
        matching_files.sort(
            key=lambda x: datetime.strptime(
                x.split("_")[-1].replace(".log", ""), "%Y-%m-%d-%H-%M-%S"
            ),
            reverse=True,
        )
        most_recent_file = matching_files[0]  # This will only be the file name
        print(f"Most recent log file: {most_recent_file}")
        return most_recent_file
    except Exception as e:
        print(f"Error retrieving log files: {e}")
        return None
       
def get_script(db: Database, script_id: str) -> JSONResponse:
    try:
        if not ObjectId.is_valid(script_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Invalid script ID.",
                    "data": None,
                },
            )
        script = db[SCRIPTS_COLLECTION].find_one({"_id": ObjectId(script_id)})
        if script:
            # Serialize datetime fields before returning
            serialized_script = serialize_datetime(script)
            print("sdfsdf")
            serialized_script["_id"] = str(serialized_script["_id"])
            recent_log = get_recent_log_file(serialized_script["script_name"])
            serialized_script["recent_log_file"] = recent_log
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Script retrieved successfully.",
                    "data": serialized_script,
                },
            )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": "Script not found.",
                "data": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error retrieving script: {e}",
                "data": None,
            },
        )

def update_script(db: Database, script_id: str, script_update: ScriptUpdate, file: Optional[UploadFile] = None) -> JSONResponse:
    try:
        if script_update.developer_id:
            developer = db[DEVELOPERS_COLLECTION].find_one({"_id": ObjectId(script_update.developer_id)})
            if not developer:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer not found")
        
        update_data = script_update.dict(exclude_unset=True)
        file_path = None
        if file:
            file_extension = file.filename.split(".")[-1]
            saved_file_name = f"{script_update.script_name}.{file_extension}"
            file_path = save_file(file, saved_file_name,update_data["script_type"])
            update_data["script_file_path"] = file_path
        else:
            result = db[SCRIPTS_COLLECTION].find_one({"_id": ObjectId(script_id)})
            file_path = result["script_file_path"]

        if not ObjectId.is_valid(script_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Invalid script ID.",
                    "data": None,
                },
            )

        result = db[SCRIPTS_COLLECTION].update_one({"_id": ObjectId(script_id)}, {"$set": update_data})

        if file or script_update.script_name or script_update.schedule_time or script_update.frequency :
            try:
                schedule_script(db, script_id, script_update.script_name, file_path, script_update.schedule_time,script_update.frequency,script_update.interval_days)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        # if result.modified_count == 1 or file:
        updated_script = db[SCRIPTS_COLLECTION].find_one({"_id": ObjectId(script_id)})
        # Serialize datetime fields before returning
        serialized_script = serialize_datetime(updated_script)
        serialized_script["_id"] = str(serialized_script["_id"])
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Script updated successfully.",
                "data": serialized_script,
            },
        )
        
        # return JSONResponse(
        #     status_code=status.HTTP_404_NOT_FOUND,
        #     content={
        #         "status": "error",
        #         "message": "Script not found or no changes made.",
        #         "data": None,
        #     },
        # )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error updating script: {e}",
                "data": None,
            },
        )

def delete_script(db: Database, script_id: str) -> JSONResponse:
    try:
        if not ObjectId.is_valid(script_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Invalid script ID.",
                    "data": None,
                },
            )
        
        script = db[SCRIPTS_COLLECTION].find_one({"_id": ObjectId(script_id)})

        if script and "script_file_path" in script:
            delete_file(script["script_file_path"])
        
        try:
            re=remove_schedule_script(db, script_id, script["script_name"])
            if re["status"] == "error":

                return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": "error",
                    "message": re["message"],
                    "data": None,
                })
        except ValueError as e:
            return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": e,
                "data": None,
            })
        result = db[SCRIPTS_COLLECTION].delete_one({"_id": ObjectId(script_id)})
        
        if result.deleted_count == 1:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Script deleted successfully.",
                    "data": None,
                },
            )
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": "Script not found.",
                "data": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error deleting script: {e}",
                "data": None,
            },
        )

def list_scripts(db: Database, limit: int = 10, page: int = 1) -> JSONResponse:
    try:
        skip = (page - 1) * limit
        total_count = db[SCRIPTS_COLLECTION].count_documents({})

        scripts_cursor = db[SCRIPTS_COLLECTION].find().skip(skip).limit(limit)
        scripts = list(scripts_cursor)
        
        for script in scripts:
            script["_id"] = str(script["_id"])
        scripts= serialize_datetime(scripts)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Scripts retrieved successfully.",
                "data": {"count":total_count,"data":scripts},
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error listing scripts: {e}",
                "data": None,
            },
        )


def get_scripts_by_developer(db: Database, developer_id: str,limit: int = 10, page: int = 1) -> JSONResponse:
    try:
        skip = (page - 1) * limit
        scripts_cursor = db[SCRIPTS_COLLECTION].find({"developer_id": developer_id}).skip(skip).limit(limit)
        scripts = list(scripts_cursor)
        
        if not scripts:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": "error",
                    "message": "No scripts found for this developer.",
                    "data": None,
                },
            )
        
        for script in scripts:
            script["_id"] = str(script["_id"])
        
       
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Scripts retrieved for developer.",
                "data": [serialize_datetime(script) for script in scripts],
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error retrieving scripts for developer: {e}",
                "data": None,
            },
        )

def get_all_scheduled_scripts(db: Database, limit: int = 10, page: int = 1) -> JSONResponse:
    try:
        skip = (page - 1) * limit
        scripts_cursor = db[SCRIPTS_SCHEDULE_COLLECTION].find().skip(skip).limit(limit)
        scripts = list(scripts_cursor) 
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Scheduled scripts retrieved.",
                "data": [
                    ScheduledScriptInDB(
                        script_name=script["script_name"],
                        schedule_time=script["schedule_time"],
                        script_file_path=script["script_file_path"],
                    ).dict()
                    for script in scripts
                    if "script_name" in script and "schedule_time" in script and "script_file_path" in script
                ],
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error retrieving scheduled scripts: {e}",
                "data": None,
            },
        )
def get_frequencies() -> JSONResponse:
    try:
    
        frequency_list= list(Frequency)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Frequency retrieved.",
                "data": frequency_list
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error retrieving Frequency: {e}",
                "data": None,
            },
        )
def get_script_type() -> JSONResponse:
    try:
    
        script_type_list= list(ScriptType)
        print("Sdfsdfsdf")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Script Type retrieved.",
                "data": script_type_list
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error retrieving Script Type: {e}",
                "data": None,
            },
        )
def add_big_refs_to_script(db: Database,data) -> JSONResponse:
    try:
        print("sdfdsfsdfdsf")
    
        existing_document = db[SCRIPTS_COLLECTION].find_one({"script_name": data.script_name})

        print("Sdfsdfsdf",existing_document)
        if existing_document:
            current_big_ref_no = existing_document.get("big_ref_no", [])
            print(current_big_ref_no)
            updated_big_ref_no = list(set(current_big_ref_no + data.big_ref_no))

            current_scrap_history = existing_document.get("scraped_data", [])
            if not type(current_scrap_history) == list:
                current_scrap_history=[]
            print(current_scrap_history)
            current_datetime = datetime.now()
            current_scrap_history.append(
                {"date": current_datetime, "scraped_count": data.scrap_count,"bigref_no":data.big_ref_no}
            )
           
            update_result = db[SCRIPTS_COLLECTION].update_one(
                {"script_name": data.script_name},
                {"$set": {"bigref_no": updated_big_ref_no,"scraped_data":current_scrap_history}}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "big_refs added.",
                
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error During big_refs  : {e}",
                "data": None,
            },
        )

