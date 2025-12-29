from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.schemas.user_schemas import UpdateUserInfoRequest, ChangePasswordRequest
from api.middleware.auth_middleware import get_current_user
from sqlalchemy import or_
from modules.admin_module.services.user_service import UserService

router = APIRouter()


@router.get("/users", response_model=PaginatedResponse)
async def get_users(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import User, UserRole, Role
    
    with db_manager.get_session() as session:
        query = session.query(User).filter(User.tenant_id == current_user["tenant_id"])
        
        if pagination.search:
            query = query.filter(or_(
                User.username.ilike(f"%{pagination.search}%"),
                User.email.ilike(f"%{pagination.search}%"),
                User.first_name.ilike(f"%{pagination.search}%"),
                User.last_name.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        users = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        user_data = []
        for user in users:
            # Get user roles
            user_roles = session.query(Role).join(UserRole).filter(
                UserRole.user_id == user.id
            ).all()
            
            roles = [role.name for role in user_roles]
            
            user_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "roles": roles,
                "role_ids": [role.id for role in user_roles]
            })
    
    return PaginatedResponse(
        success=True,
        message="Users retrieved successfully",
        data=user_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/users", response_model=BaseResponse)
async def create_user(user_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole
    
    user_service = UserService()
    user_id = user_service.create(user_data)
    
    # Create user role mappings if roles are provided
    if "role_ids" in user_data and user_data["role_ids"]:
        with db_manager.get_session() as session:
            for role_id in user_data["role_ids"]:
                user_role = UserRole(
                    user_id=user_id,
                    role_id=role_id,
                    tenant_id=current_user["tenant_id"]
                )
                session.add(user_role)
            session.commit()
    
    return BaseResponse(
        success=True,
        message="User created successfully",
        data={"id": user_id}
    )


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


@router.post("/users/import", response_model=BaseResponse)
async def import_users(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole, Role
    
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    user_service = UserService()
    imported_count = 0
    
    for row in csv_data:
        try:
            user_id = user_service.create({
                "username": row["username"],
                "email": row["email"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "password": row["password"],
                "is_active": row["is_active"].lower() == "true"
            })
            
            # Handle role assignments if provided
            if "role_names" in row and row["role_names"].strip():
                role_names = [name.strip() for name in row["role_names"].split(",")]
                with db_manager.get_session() as session:
                    for role_name in role_names:
                        role = session.query(Role).filter(
                            Role.name == role_name,
                            Role.tenant_id == current_user["tenant_id"]
                        ).first()
                        if role:
                            user_role = UserRole(
                                user_id=user_id,
                                role_id=role.id,
                                tenant_id=current_user["tenant_id"]
                            )
                            session.add(user_role)
                    session.commit()
            
            imported_count += 1
        except Exception:
            continue
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} users successfully"
    )


@router.get("/users/{user_id}", response_model=BaseResponse)
async def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import User
    
    with db_manager.get_session() as session:
        user = session.query(User).filter(
            User.id == user_id,
            User.tenant_id == current_user["tenant_id"]
        ).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active
        }
    
    return BaseResponse(
        success=True,
        message="User retrieved successfully",
        data=user_data
    )


@router.put("/users/{user_id}", response_model=BaseResponse)
async def update_user(user_id: int, user_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole
    
    user_service = UserService()
    user = user_service.update(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user role mappings if roles are provided
    if "role_ids" in user_data:
        with db_manager.get_session() as session:
            # Delete existing role mappings
            session.query(UserRole).filter(UserRole.user_id == user_id).delete()
            
            # Create new role mappings
            if user_data["role_ids"]:
                for role_id in user_data["role_ids"]:
                    user_role = UserRole(
                        user_id=user_id,
                        role_id=role_id,
                        tenant_id=current_user["tenant_id"]
                    )
                    session.add(user_role)
            session.commit()
    
    return BaseResponse(success=True, message="User updated successfully")


@router.delete("/users/{user_id}", response_model=BaseResponse)
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    user_service = UserService()
    success = user_service.delete(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return BaseResponse(success=True, message="User deleted successfully")


@router.patch("/users/{user_id}/info", response_model=BaseResponse)
async def update_user_info(user_id: int, request: UpdateUserInfoRequest, current_user: dict = Depends(get_current_user)):
    user_service = UserService()
    data = request.model_dump(exclude_unset=True)
    success = user_service.update_user_info(user_id, data, current_user["tenant_id"])
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return BaseResponse(success=True, message="User information updated successfully")


@router.patch("/users/{user_id}/password", response_model=BaseResponse)
async def change_user_password(user_id: int, request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    user_service = UserService()
    success = user_service.change_password(
        user_id, 
        request.current_password, 
        request.new_password, 
        current_user["tenant_id"]
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid current password or user not found")
    
    return BaseResponse(success=True, message="Password changed successfully")
