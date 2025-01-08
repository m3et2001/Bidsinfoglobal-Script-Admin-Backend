from typing import List, Optional
from bson import ObjectId
from pymongo.database import Database
from .models import DeveloperCreate, DeveloperUpdate, DeveloperInDB
from fastapi import HTTPException

DEVELOPERS_COLLECTION = "developers"

def create_developer(db: Database, developer: DeveloperCreate) -> DeveloperInDB:
    try:
        developer_dict = developer.dict()
        result = db[DEVELOPERS_COLLECTION].insert_one(developer_dict)
        developer_dict["_id"] = str(result.inserted_id)
        return DeveloperInDB(**developer_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating developer: {e}")

def get_developer(db: Database, developer_id: str) -> Optional[DeveloperInDB]:
    try:
        if not ObjectId.is_valid(developer_id):
            return None
        developer = db[DEVELOPERS_COLLECTION].find_one({"_id": ObjectId(developer_id)})
        if developer:
            developer["_id"] = str(developer["_id"])
            return DeveloperInDB(**developer)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving developer: {e}")

def update_developer(db: Database, developer_id: str, developer_update: DeveloperUpdate) -> Optional[DeveloperInDB]:
    try:
        update_data = developer_update.dict(exclude_unset=True)
        if not ObjectId.is_valid(developer_id):
            return None
        result = db[DEVELOPERS_COLLECTION].update_one({"_id": ObjectId(developer_id)}, {"$set": update_data})
        if result.modified_count == 1:
            return get_developer(db, developer_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating developer: {e}")

def delete_developer(db: Database, developer_id: str) -> bool:
    try:
        if not ObjectId.is_valid(developer_id):
            return False
        result = db[DEVELOPERS_COLLECTION].delete_one({"_id": ObjectId(developer_id)})
        return result.deleted_count == 1
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting developer: {e}")

def list_developers(db: Database, limit: int = 100) -> List[DeveloperInDB]:
    try:
        developers_cursor = db[DEVELOPERS_COLLECTION].find().limit(limit)
        developers = list(developers_cursor)
        for developer in developers:
            developer["_id"] = str(developer["_id"])
        return [DeveloperInDB(**developer) for developer in developers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing developers: {e}")
