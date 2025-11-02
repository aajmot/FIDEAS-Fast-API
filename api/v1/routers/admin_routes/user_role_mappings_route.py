
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from sqlalchemy import or_
from modules.admin_module.services.user_service import UserService

router = APIRouter()
# User Role Mapping endpoints
@router.get("/user-role-mappings/role/{role_id}", response_model=BaseResponse)
async def get_role_users(role_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole, User
    
    with db_manager.get_session() as session:
        user_mappings = session.query(UserRole, User).join(
            User, UserRole.user_id == User.id
        ).filter(
            UserRole.role_id == role_id
        ).all()
        
        users = [{
            "user_id": mapping.User.id,
            "username": mapping.User.username,
            "full_name": f"{mapping.User.first_name} {mapping.User.last_name}"
        } for mapping in user_mappings]
        
        return BaseResponse(
            success=True,
            message="Role users retrieved successfully",
            data=users
        )


@router.get("/user-role-mappings", response_model=PaginatedResponse)
async def get_user_role_mappings(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole, User, Role
    
    with db_manager.get_session() as session:
        # Get only roles that have users assigned
        query = session.query(Role).join(UserRole).filter(
            Role.tenant_id == current_user["tenant_id"]
        ).distinct()
        
        if pagination.search:
            query = query.filter(or_(
                Role.name.ilike(f"%{pagination.search}%"),
                Role.description.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        roles_with_users = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        role_data = []
        for role in roles_with_users:
            # Get users assigned to this role
            user_mappings = session.query(UserRole, User).join(
                User, UserRole.user_id == User.id
            ).filter(
                UserRole.role_id == role.id
            ).all()
            
            users = [{
                "mapping_id": mapping.UserRole.id,
                "user_id": mapping.User.id,
                "username": mapping.User.username,
                "full_name": f"{mapping.User.first_name} {mapping.User.last_name}"
            } for mapping in user_mappings]
            
            role_data.append({
                "role_id": role.id,
                "role_name": role.name,
                "role_description": role.description,
                "user_count": len(users),
                "users": users
            })
    
    return PaginatedResponse(
        success=True,
        message="Role-wise user mappings retrieved successfully",
        data=role_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/user-role-mappings", response_model=BaseResponse)
async def create_user_role_mapping(mapping_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole
    
    with db_manager.get_session() as session:
        existing = session.query(UserRole).filter(
            UserRole.user_id == mapping_data["user_id"],
            UserRole.role_id == mapping_data["role_id"]
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="User role mapping already exists")
        
        user_role = UserRole(
            user_id=mapping_data["user_id"],
            role_id=mapping_data["role_id"],
            tenant_id=current_user["tenant_id"]
        )
        session.add(user_role)
        session.commit()
        
        return BaseResponse(
            success=True,
            message="User role mapping created successfully",
            data={"id": user_role.id}
        )


@router.delete("/user-role-mappings/{mapping_id}", response_model=BaseResponse)
async def delete_user_role_mapping(mapping_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole
    
    with db_manager.get_session() as session:
        mapping = session.query(UserRole).filter(UserRole.id == mapping_id).first()
        if not mapping:
            raise HTTPException(status_code=404, detail="User role mapping not found")
        
        session.delete(mapping)
        session.commit()
        
        return BaseResponse(success=True, message="User role mapping deleted successfully")


@router.post("/user-role-mappings/bulk-delete", response_model=BaseResponse)
async def bulk_delete_user_role_mappings(mapping_ids: List[int], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole
    
    with db_manager.get_session() as session:
        deleted_count = session.query(UserRole).filter(UserRole.id.in_(mapping_ids)).delete(synchronize_session=False)
        session.commit()
        
        return BaseResponse(
            success=True, 
            message=f"Deleted {deleted_count} user role mappings successfully"
        )


@router.delete("/user-role-mappings/role/{role_id}", response_model=BaseResponse)
async def delete_all_users_from_role(role_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole
    
    with db_manager.get_session() as session:
        deleted_count = session.query(UserRole).filter(UserRole.role_id == role_id).delete()
        session.commit()
        
        return BaseResponse(
            success=True,
            message=f"Removed all users from role successfully"
        )


@router.put("/user-role-mappings/role/{role_id}", response_model=BaseResponse)
async def update_role_users(role_id: int, user_ids: List[int], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole
    
    with db_manager.get_session() as session:
        # Delete existing mappings for this role
        session.query(UserRole).filter(UserRole.role_id == role_id).delete()
        
        # Create new mappings
        for user_id in user_ids:
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                tenant_id=current_user["tenant_id"]
            )
            session.add(user_role)
        
        session.commit()
        
        return BaseResponse(
            success=True,
            message="Role users updated successfully"
        )


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


@router.post("/user-role-mappings/import", response_model=BaseResponse)
async def import_user_role_mappings(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import UserRole, Role, User
    
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    imported_count = 0
    
    with db_manager.get_session() as session:
        for row in csv_data:
            try:
                role_name = row["role_name"].strip()
                usernames = [u.strip() for u in row["usernames"].split(",") if u.strip()]
                
                # Find role
                role = session.query(Role).filter(
                    Role.name == role_name,
                    Role.tenant_id == current_user["tenant_id"]
                ).first()
                
                if not role or not usernames:
                    continue
                
                # Clear existing mappings for this role
                session.query(UserRole).filter(UserRole.role_id == role.id).delete()
                
                # Add new mappings
                for username in usernames:
                    user = session.query(User).filter(
                        User.username == username,
                        User.tenant_id == current_user["tenant_id"]
                    ).first()
                    
                    if user:
                        user_role = UserRole(
                            user_id=user.id,
                            role_id=role.id,
                            tenant_id=current_user["tenant_id"]
                        )
                        session.add(user_role)
                
                imported_count += 1
            except Exception:
                continue
        
        session.commit()
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} role mappings successfully"
    )
