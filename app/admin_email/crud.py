# crud.py

from typing import List, Optional
from bson import ObjectId
from pymongo.database import Database
from .models import AdminCreate, AdminUpdate, AdminInDB
from fastapi import HTTPException
import os

ADMINS_COLLECTION = "admins"

def create_admin(db: Database, admin: AdminCreate) -> AdminInDB:
    try:
        admin_dict = admin.dict()
        result = db[ADMINS_COLLECTION].insert_one(admin_dict)
        admin_dict["_id"] = str(result.inserted_id)
        return AdminInDB(**admin_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating admin: {e}")

def get_admin(db: Database, admin_id: str) -> Optional[AdminInDB]:
    try:
        if not ObjectId.is_valid(admin_id):
            return None
        admin = db[ADMINS_COLLECTION].find_one({"_id": ObjectId(admin_id)})
        if admin:
            admin["_id"] = str(admin["_id"])
            return AdminInDB(**admin)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving admin: {e}")

def update_admin(db: Database, admin_id: str, admin_update: AdminUpdate) -> Optional[AdminInDB]:
    try:
        update_data = admin_update.dict(exclude_unset=True)
        if not ObjectId.is_valid(admin_id):
            return None
        result = db[ADMINS_COLLECTION].update_one({"_id": ObjectId(admin_id)}, {"$set": update_data})
        if result.modified_count == 1:
            return get_admin(db, admin_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating admin: {e}")

def delete_admin(db: Database, admin_id: str) -> bool:
    try:
        if not ObjectId.is_valid(admin_id):
            return False
        result = db[ADMINS_COLLECTION].delete_one({"_id": ObjectId(admin_id)})
        return result.deleted_count == 1
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting admin: {e}")

def list_admins(db: Database, limit: int = 100) -> List[AdminInDB]:
    try:
        admins_cursor = db[ADMINS_COLLECTION].find().limit(limit)
        admins = list(admins_cursor)
        for admin in admins:
            admin["_id"] = str(admin["_id"])
        return [AdminInDB(**admin) for admin in admins]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing admins: {e}")
