from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
import io
import csv

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.core.utils.pagination import PaginationParams, PaginatedResponse
from app.modules.admin.services.user_service import UserService

router = APIRouter()

@router.get("/users")
async def get_users(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.db.models.admin_models.user_model import User
    
    query = db.query(User).filter(User.tenant_id == current_user["tenant_id"])
    
    if pagination.search:
        query = query.filter(or_(
            User.username.ilike(f"%{pagination.search}%"),
            User.email.ilike(f"%{pagination.search}%"),
            User.first_name.ilike(f"%{pagination.search}%"),
            User.last_name.ilike(f"%{pagination.search}%")
        ))
    
    total = query.count()
    users = query.offset(pagination.offset).limit(pagination.size).all()
    
    user_data = [{
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active
    } for user in users]
    
    return PaginatedResponse.create(
        items=user_data,
        total=total,
        page=pagination.page,
        size=pagination.size
    )

@router.post("/users")
async def create_user(
    user_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = user_service.create(user_data)
    return APIResponse.created({"id": user.id})

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return APIResponse.success({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active
    })

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = user_service.update(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return APIResponse.success(message="User updated successfully")

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    success = user_service.delete(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return APIResponse.success(message="User deleted successfully")

@router.get("/users/export-template")
async def export_users_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["username", "email", "first_name", "last_name", "password", "is_active", "role_names"])
    writer.writerow(["john_doe", "john@example.com", "John", "Doe", "password123", "true", "Admin,Manager"])
    
    output.seek(0)
    content = output.getvalue()
    
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_template.csv"}
    )

@router.post("/users/import")
async def import_users(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    user_service = UserService(db)
    imported_count = 0
    
    for row in csv_data:
        try:
            user_data = {
                "username": row["username"],
                "email": row["email"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "password": row["password"],
                "is_active": row["is_active"].lower() == "true"
            }
            user_service.create(user_data)
            imported_count += 1
        except Exception:
            continue
    
    return APIResponse.success(message=f"Imported {imported_count} users successfully")