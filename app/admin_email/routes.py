# admin_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from db import get_database
from .crud import create_admin, get_admin, update_admin, delete_admin, list_admins
from .models import AdminCreate, AdminUpdate, AdminInDB
from utils.utils import get_current_user

router = APIRouter()

@router.post("/", response_description="Create a new admin", response_model=AdminInDB, status_code=status.HTTP_201_CREATED)
def create_admin_endpoint(admin: AdminCreate, db=Depends(get_database), user: str = Depends(get_current_user)):
    new_admin = create_admin(db, admin)
    return new_admin

@router.get("/{admin_id}", response_description="Get admin by ID", response_model=AdminInDB)
def get_admin_endpoint(admin_id: str, db=Depends(get_database), user: str = Depends(get_current_user)):
    admin = get_admin(db, admin_id)
    if admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    return admin

@router.put("/{admin_id}", response_description="Update an admin", response_model=AdminInDB)
def update_admin_endpoint(admin_id: str, admin_update: AdminUpdate, db=Depends(get_database), user: str = Depends(get_current_user)):
    updated_admin = update_admin(db, admin_id, admin_update)
    if updated_admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found or no changes made")
    return updated_admin

@router.delete("/{admin_id}", response_description="Delete an admin")
def delete_admin_endpoint(admin_id: str, db=Depends(get_database), user: str = Depends(get_current_user)):
    deleted = delete_admin(db, admin_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    return {"message": "Admin deleted successfully"}

@router.get("/", response_description="List all admins", response_model=List[AdminInDB])
def list_admins_endpoint(db=Depends(get_database), limit: int = 100, user: str = Depends(get_current_user)):
    admins = list_admins(db, limit)
    return admins
