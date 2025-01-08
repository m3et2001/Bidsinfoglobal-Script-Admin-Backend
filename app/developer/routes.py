from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException, status,File
from typing import List
from db import get_database
from .crud import create_developer, get_developer, update_developer, delete_developer, list_developers
from .models import DeveloperCreate, DeveloperUpdate, DeveloperInDB, DeveloperStatus
from datetime import date
from typing import Optional
from utils.utils import get_current_user

router = APIRouter()

@router.post("/", response_description="Create a new developer", response_model=DeveloperInDB, status_code=status.HTTP_201_CREATED)
def create_developer_endpoint(
    db=Depends(get_database),
    name: str = Form(...),
    joining_date: date = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    address: str = Form(...),
    total_script_count: int = Form(...),
    active_script_count: int = Form(...),
    maintain_script_count: int = Form(...),
    status: DeveloperStatus = Form(...),
     user: str = Depends(get_current_user)
):
    developer_data = DeveloperCreate(
        name=name,
        joining_date=joining_date,
        email=email,
        phone_number=phone_number,
        address=address,
        total_script_count=total_script_count,
        active_script_count=active_script_count,
        maintain_script_count=maintain_script_count,
        status=status
    )
    new_developer = create_developer(db, developer_data)
    return new_developer

@router.get("/{developer_id}", response_description="Get a developer by ID", response_model=DeveloperInDB)
def get_developer_endpoint(developer_id: str, db=Depends(get_database), user: str = Depends(get_current_user)):
    developer = get_developer(db, developer_id)
    if developer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer not found")
    return developer

@router.put("/{developer_id}", response_description="Update a developer", response_model=DeveloperInDB)
def update_developer_endpoint(
  developer_id: str,
  db=Depends(get_database),
  name: Optional[str] = Form(None),
  joining_date: Optional[date] = Form(None),
  email: Optional[str] = Form(None),
  phone_number: Optional[str] = Form(None),
  address: Optional[str] = Form(None),
  total_script_count: Optional[int] = Form(None),
  active_script_count: Optional[int] = Form(None),
  maintain_script_count: Optional[int] = Form(None),
  status: Optional[DeveloperStatus] = Form(None),
   user: str = Depends(get_current_user)
):
    developer_update = DeveloperUpdate(
        name=name,
        joining_date=joining_date,
        email=email,
        phone_number=phone_number,
        address=address,
        total_script_count=total_script_count,
        active_script_count=active_script_count,
        maintain_script_count=maintain_script_count,
        status=status
    )
    updated_developer = update_developer(db, developer_id, developer_update)
    if updated_developer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer not found or no changes made")
    return updated_developer

@router.delete("/{developer_id}", response_description="Delete a developer")
def delete_developer_endpoint(developer_id: str, db=Depends(get_database), user: str = Depends(get_current_user)):
    deleted = delete_developer(db, developer_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer not found")
    return {"message": "Developer deleted successfully"}

@router.get("/", response_description="List all developers", response_model=List[DeveloperInDB])
def list_developers_endpoint(db=Depends(get_database), limit: int = 100, user: str = Depends(get_current_user)):
    developers = list_developers(db, limit)
    return developers
