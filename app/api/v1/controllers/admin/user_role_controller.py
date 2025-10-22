from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
import io
import csv
import math

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.core.utils.pagination import PaginationParams, PaginatedResponse
from app.modules.admin.services.user_role_service import UserRoleService

router = APIRouter()

@router.get("/user-role-mappings")
async def get_user_role_mappings(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role_service = UserRoleService(db)
    role_data, total = user_role_service.get_role_mappings_paginated(
        current_user["tenant_id"], 
        pagination.search, 
        pagination.offset, 
        pagination.size
    )
    
    return PaginatedResponse.create(
        items=role_data,
        total=total,
        page=pagination.page,
        size=pagination.size
    )

@router.get("/user-role-mappings/role/{role_id}")
async def get_role_users(
    role_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role_service = UserRoleService(db)
    users = user_role_service.get_role_users(role_id)
    return APIResponse.success(users)

@router.post("/user-role-mappings")
async def create_user_role_mapping(
    mapping_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role_service = UserRoleService(db)
    user_role = user_role_service.create_mapping(
        mapping_data["user_id"],
        mapping_data["role_id"],
        current_user["tenant_id"],
        current_user["username"]
    )
    
    if not user_role:
        raise HTTPException(status_code=400, detail="User role mapping already exists")
    
    return APIResponse.created({"id": user_role.id})

@router.delete("/user-role-mappings/{mapping_id}")
async def delete_user_role_mapping(
    mapping_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role_service = UserRoleService(db)
    success = user_role_service.delete_mapping(mapping_id)
    if not success:
        raise HTTPException(status_code=404, detail="User role mapping not found")
    
    return APIResponse.success(message="User role mapping deleted successfully")

@router.post("/user-role-mappings/bulk-delete")
async def bulk_delete_user_role_mappings(
    mapping_ids: List[int],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role_service = UserRoleService(db)
    deleted_count = user_role_service.bulk_delete_mappings(mapping_ids)
    
    return APIResponse.success(message=f"Deleted {deleted_count} user role mappings successfully")

@router.delete("/user-role-mappings/role/{role_id}")
async def delete_all_users_from_role(
    role_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role_service = UserRoleService(db)
    user_role_service.delete_all_role_users(role_id)
    
    return APIResponse.success(message="Removed all users from role successfully")

@router.put("/user-role-mappings/role/{role_id}")
async def update_role_users(
    role_id: int,
    user_ids: List[int],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role_service = UserRoleService(db)
    user_role_service.update_role_users(
        role_id, 
        user_ids, 
        current_user["tenant_id"], 
        current_user["username"]
    )
    
    return APIResponse.success(message="Role users updated successfully")

@router.get("/user-role-mappings/export-template")
async def export_user_role_mappings_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["role_name", "usernames"])
    writer.writerow(["Admin", "john_doe,jane_smith"])
    writer.writerow(["Manager", "bob_wilson"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=user_role_mappings_template.csv"}
    )

@router.post("/user-role-mappings/import")
async def import_user_role_mappings(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    user_role_service = UserRoleService(db)
    mappings_data = list(csv_data)
    imported_count = user_role_service.import_mappings(
        mappings_data, 
        current_user["tenant_id"], 
        current_user["username"]
    )
    
    return APIResponse.success(message=f"Imported {imported_count} role mappings successfully")