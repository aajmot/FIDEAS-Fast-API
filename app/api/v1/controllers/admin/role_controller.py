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
from app.modules.admin.services.role_service import RoleService

router = APIRouter()

@router.get("/roles")
async def get_roles(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role_service = RoleService(db)
    filters = {"tenant_id": current_user["tenant_id"]}
    roles = role_service.get_all(filters)
    
    role_data = [{
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active
    } for role in roles]
    
    return PaginatedResponse.create(
        items=role_data,
        total=len(role_data),
        page=pagination.page,
        size=pagination.size
    )

@router.post("/roles")
async def create_role(
    role_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role_service = RoleService(db)
    role_data["tenant_id"] = current_user["tenant_id"]
    role_data["created_by"] = current_user["username"]
    role = role_service.create(role_data)
    return APIResponse.created({"id": role.id})

@router.get("/roles/{role_id}")
async def get_role(
    role_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role_service = RoleService(db)
    role = role_service.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return APIResponse.success({
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active
    })

@router.put("/roles/{role_id}")
async def update_role(
    role_id: int,
    role_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role_service = RoleService(db)
    role_data["updated_by"] = current_user["username"]
    role = role_service.update(role_id, role_data)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return APIResponse.success(message="Role updated successfully")

@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role_service = RoleService(db)
    success = role_service.delete(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return APIResponse.success(message="Role deleted successfully")

@router.get("/roles/export-template")
async def export_roles_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "description", "is_active"])
    writer.writerow(["Manager", "Management role", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=roles_template.csv"}
    )

@router.post("/roles/import")
async def import_roles(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    role_service = RoleService(db)
    roles_data = list(csv_data)
    imported_count = role_service.import_roles(roles_data, current_user["tenant_id"], current_user["username"])
    
    return APIResponse.success(message=f"Imported {imported_count} roles successfully")