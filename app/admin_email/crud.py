from typing import List, Optional
from bson import ObjectId
from pymongo.database import Database
from .models import AdminCreate, AdminUpdate, AdminInDB
from fastapi import  status
from fastapi.responses import JSONResponse

ADMINS_COLLECTION = "admins"

def create_admin(db: Database, admin: AdminCreate) -> JSONResponse:
    try:
        admin_dict = admin.dict()
        result = db[ADMINS_COLLECTION].insert_one(admin_dict)
        admin_dict["_id"] = str(result.inserted_id)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "message": "Admin created successfully.",
                "data": AdminInDB(**admin_dict).dict(),
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error creating admin: {e}",
                "data": None,
            },
        )

def get_admin(db: Database, admin_id: str) -> JSONResponse:
    try:
        if not ObjectId.is_valid(admin_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Invalid admin ID",
                    "data": None,
                },
            )
        admin = db[ADMINS_COLLECTION].find_one({"_id": ObjectId(admin_id)})
        if admin:
            admin["_id"] = str(admin["_id"])
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Admin retrieved successfully.",
                    "data": AdminInDB(**admin).dict(),
                },
            )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": "Admin not found",
                "data": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error retrieving admin: {e}",
                "data": None,
            },
        )

def update_admin(db: Database, admin_id: str, admin_update: AdminUpdate) -> JSONResponse:
    try:
        update_data = admin_update.dict(exclude_unset=True)
        if not ObjectId.is_valid(admin_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Invalid admin ID",
                    "data": None,
                },
            )
        result = db[ADMINS_COLLECTION].update_one({"_id": ObjectId(admin_id)}, {"$set": update_data})
        return get_admin(db, admin_id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error updating admin: {e}",
                "data": None,
            },
        )

def delete_admin(db: Database, admin_id: str) -> JSONResponse:
    try:
        if not ObjectId.is_valid(admin_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Invalid admin ID",
                    "data": None,
                },
            )
        result = db[ADMINS_COLLECTION].delete_one({"_id": ObjectId(admin_id)})
        if result.deleted_count == 1:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Admin deleted successfully.",
                    "data": None,
                },
            )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": "Admin deletion failed",
                "data": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error deleting admin: {e}",
                "data": None,
            },
        )

def list_admins(db: Database, limit: int = 10, page: int = 1) -> JSONResponse:
    try:
        skip = (page - 1) * limit
        admins_cursor = db[ADMINS_COLLECTION].find().skip(skip).limit(limit)
        admins = list(admins_cursor)
        for admin in admins:
            admin["_id"] = str(admin["_id"])
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Admins retrieved successfully.",
                "data": [AdminInDB(**admin).dict() for admin in admins],
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error listing admins: {e}",
                "data": None,
            },
        )
