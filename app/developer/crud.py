from typing import List, Optional
from bson import ObjectId
from pymongo.database import Database
from .models import DeveloperCreate, DeveloperUpdate, DeveloperInDB
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
import datetime

DEVELOPERS_COLLECTION = "developers"

# Utility function to handle datetime serialization
def serialize_datetime(data):
    if isinstance(data, datetime.datetime):
        return data.isoformat()  # Convert datetime to ISO string
    if isinstance(data, list):
        return [serialize_datetime(item) for item in data]
    if isinstance(data, dict):
        return {key: serialize_datetime(value) for key, value in data.items()}
    return data

def create_developer(db: Database, developer: DeveloperCreate) -> JSONResponse:
    try:
        developer_dict = developer.dict()
        result = db[DEVELOPERS_COLLECTION].insert_one(developer_dict)
        developer_dict["_id"] = str(result.inserted_id)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "message": "Developer created successfully.",
                "data": serialize_datetime(DeveloperInDB(**developer_dict).dict()),  # Apply datetime serialization
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error creating developer: {str(e)}",
                "data": None,
            },
        )

def get_developer(db: Database, developer_id: str) -> JSONResponse:
    try:
        if not ObjectId.is_valid(developer_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Invalid developer ID.",
                    "data": None,
                },
            )
        developer = db[DEVELOPERS_COLLECTION].find_one({"_id": ObjectId(developer_id)})
        if developer:
            developer["_id"] = str(developer["_id"])
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Developer retrieved successfully.",
                    "data": serialize_datetime(DeveloperInDB(**developer).dict()),  # Apply datetime serialization
                },
            )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": "Developer not found.",
                "data": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error retrieving developer: {str(e)}",
                "data": None,
            },
        )

def update_developer(db: Database, developer_id: str, developer_update: DeveloperUpdate) -> JSONResponse:
    try:
        update_data = developer_update.dict(exclude_unset=True)
        if not ObjectId.is_valid(developer_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Invalid developer ID.",
                    "data": None,
                },
            )
        result = db[DEVELOPERS_COLLECTION].update_one(
            {"_id": ObjectId(developer_id)}, {"$set": update_data}
        )
        if result.modified_count == 1:
            updated_developer = db[DEVELOPERS_COLLECTION].find_one(
                {"_id": ObjectId(developer_id)}
            )
            updated_developer["_id"] = str(updated_developer["_id"])
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Developer updated successfully.",
                    "data": serialize_datetime(DeveloperInDB(**updated_developer).dict()),  # Apply datetime serialization
                },
            )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": "Developer not found or no changes made.",
                "data": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error updating developer: {str(e)}",
                "data": None,
            },
        )

def delete_developer(db: Database, developer_id: str) -> JSONResponse:
    try:
        if not ObjectId.is_valid(developer_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Invalid developer ID.",
                    "data": None,
                },
            )
        result = db[DEVELOPERS_COLLECTION].delete_one({"_id": ObjectId(developer_id)})
        if result.deleted_count == 1:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Developer deleted successfully.",
                    "data": None,
                },
            )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": "Developer not found.",
                "data": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error deleting developer: {str(e)}",
                "data": None,
            },
        )

def list_developers(db: Database, limit: int = 10, page: int = 1) -> JSONResponse:
    try:
        skip = (page - 1) * limit
        total_count = db[DEVELOPERS_COLLECTION].count_documents({})
        developers_cursor = db[DEVELOPERS_COLLECTION].find().skip(skip).limit(limit)
        developers = list(developers_cursor)
        for developer in developers:
            developer["_id"] = str(developer["_id"])
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Developers retrieved successfully.",
                "data": {"count":total_count,"data":serialize_datetime([DeveloperInDB(**developer).dict() for developer in developers])},  # Apply datetime serialization
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error listing developers: {str(e)}",
                "data": None,
            },
        )
