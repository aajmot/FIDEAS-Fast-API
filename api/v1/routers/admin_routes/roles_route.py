from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Dict, Any
from fastapi.responses import StreamingResponse
import io
import csv
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
from api.middleware.auth_middleware import get_current_user
from modules.admin_module.services.role_service import RoleService

router = APIRouter()


@router.get("/roles", response_model=PaginatedResponse)
async def get_roles(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import Role

    with db_manager.get_session() as session:
        query = session.query(Role).filter(Role.tenant_id == current_user["tenant_id"])

        if pagination.search:
            query = query.filter(or_(
                Role.name.ilike(f"%{pagination.search}%"),
                Role.description.ilike(f"%{pagination.search}%")
            ))

        total = query.count()
        roles = query.offset(pagination.offset).limit(pagination.per_page).all()

        role_data = [{
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active
        } for role in roles]

    return PaginatedResponse(
        success=True,
        message="Roles retrieved successfully",
        data=role_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


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


@router.post("/roles/import", response_model=BaseResponse)
async def import_roles(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    role_service = RoleService()
    imported_count = 0

    for row in csv_data:
        try:
            role_service.create({
                "name": row["name"],
                "description": row["description"],
                "is_active": row["is_active"].lower() == "true"
            })
            imported_count += 1
        except Exception:
            continue

    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} roles successfully"
    )


@router.post("/roles", response_model=BaseResponse)
async def create_role(role_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    role_service = RoleService()
    role = role_service.create(role_data)
    role_id = role.id
    return BaseResponse(
        success=True,
        message="Role created successfully",
        data={"id": role_id}
    )


@router.get("/roles/{role_id}", response_model=BaseResponse)
async def get_role(role_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import Role

    with db_manager.get_session() as session:
        role = session.query(Role).filter(
            Role.id == role_id,
            Role.tenant_id == current_user["tenant_id"]
        ).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        role_data = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active
        }

    return BaseResponse(
        success=True,
        message="Role retrieved successfully",
        data=role_data
    )


@router.put("/roles/{role_id}", response_model=BaseResponse)
async def update_role(role_id: int, role_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    role_service = RoleService()
    role = role_service.update(role_id, role_data)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return BaseResponse(success=True, message="Role updated successfully")


@router.delete("/roles/{role_id}", response_model=BaseResponse)
async def delete_role(role_id: int, current_user: dict = Depends(get_current_user)):
    role_service = RoleService()
    success = role_service.delete(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")

    return BaseResponse(success=True, message="Role deleted successfully")
