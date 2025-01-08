from typing import List, Optional
from bson import ObjectId
from pymongo.database import Database
from .models import ScriptCreate, ScriptUpdate, ScriptInDB
from fastapi import UploadFile, HTTPException
import os
from ..developer.crud import DEVELOPERS_COLLECTION

SCRIPTS_COLLECTION = "scripts"
UPLOAD_DIRECTORY = "uploaded_scripts/"

def save_file(file: UploadFile) -> str:
    try:
        if not os.path.exists(UPLOAD_DIRECTORY):
            os.makedirs(UPLOAD_DIRECTORY)
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")

def create_script(db: Database, script: ScriptCreate, file: UploadFile) -> ScriptInDB:
    try:
        print(script.developer_id)
        developer = db[DEVELOPERS_COLLECTION].find_one({"_id": ObjectId(script.developer_id)})
        if not developer:
            raise HTTPException(status_code=404, detail="Developer not found")
        file_path = save_file(file)
        script_dict = script.dict()
        script_dict["script_file_path"] = file_path
        result = db[SCRIPTS_COLLECTION].insert_one(script_dict)
        script_dict["_id"] = str(result.inserted_id)
        return ScriptInDB(**script_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating script: {e}")

def get_script(db: Database, script_id: str) -> Optional[ScriptInDB]:
    try:
        if not ObjectId.is_valid(script_id):
            return None
        script = db[SCRIPTS_COLLECTION].find_one({"_id": ObjectId(script_id)})
        if script:
            script["_id"] = str(script["_id"])
            return ScriptInDB(**script)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving script: {e}")

def update_script(db: Database, script_id: str, script_update: ScriptUpdate, file: Optional[UploadFile] = None) -> Optional[ScriptInDB]:
    try:
        if script_update.developer_id:
            developer = db[DEVELOPERS_COLLECTION].find_one({"_id": ObjectId(script_update.developer_id)})
            if not developer:
                raise HTTPException(status_code=404, detail="Developer not found")
        update_data = script_update.dict(exclude_unset=True)
        if file:
            file_path = save_file(file)
            update_data["script_file_path"] = file_path
        if not ObjectId.is_valid(script_id):
            return None
        result = db[SCRIPTS_COLLECTION].update_one({"_id": ObjectId(script_id)}, {"$set": update_data})
        if result.modified_count == 1:
            return get_script(db, script_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating script: {e}")

def delete_script(db: Database, script_id: str) -> bool:
    try:
        if not ObjectId.is_valid(script_id):
            return False
        result = db[SCRIPTS_COLLECTION].delete_one({"_id": ObjectId(script_id)})
        return result.deleted_count == 1
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting script: {e}")

def list_scripts(db: Database, limit: int = 100) -> List[ScriptInDB]:
    try:
        scripts_cursor = db[SCRIPTS_COLLECTION].find().limit(limit)
        scripts = list(scripts_cursor)
        for script in scripts:
            script["_id"] = str(script["_id"])
        # return [script for script in scripts]
        return [ScriptInDB(**script) for script in scripts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing scripts: {e}")

def get_scripts_by_developer(db: Database, developer_id: str) -> List[ScriptInDB]:
    try:
        # Fetch scripts where developer_name matches the provided one
        scripts_cursor = db[SCRIPTS_COLLECTION].find({"developer_id": developer_id})
        scripts = list(scripts_cursor)
        
        if not scripts:
            raise HTTPException(status_code=404, detail="No scripts found for this developer")
        
        # Convert ObjectId to string and return scripts
        for script in scripts:
            script["_id"] = str(script["_id"])
        
        return [ScriptInDB(**script) for script in scripts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving scripts for developer: {e}")