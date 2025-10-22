from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
import math
from api.middleware.auth_middleware import get_current_user
from modules.admin_module.services.user_service import UserService
from modules.admin_module.services.role_service import RoleService
from modules.admin_module.services.agency_service import AgencyService
from modules.admin_module.services.menu_service import MenuService
from api.v1.routers.order_commission import router as order_commission_router

router = APIRouter()

# Menu endpoints
@router.get("/menus", response_model=BaseResponse)
async def get_user_menus(current_user: dict = Depends(get_current_user)):
    """Get menus accessible to the current user based on roles"""
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import User
    
    with db_manager.get_session() as session:
        user = session.query(User).filter(
            User.id == current_user["user_id"],
            User.tenant_id == current_user["tenant_id"]
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is tenant admin
        if user.is_tenant_admin:
            # Tenant admin gets all menus
            menus = MenuService.get_user_menus(current_user["user_id"], current_user["tenant_id"])
        else:
            # Regular user gets menus based on assigned roles (union of all role permissions)
            menus = MenuService.get_user_menus(current_user["user_id"], current_user["tenant_id"])
        
        return BaseResponse(
            success=True,
            message="Menus retrieved successfully",
            data=menus
        )

# User endpoints
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

# Role endpoints
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

# Tenant endpoints
@router.get("/tenant", response_model=BaseResponse)
async def get_tenant(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import Tenant
    
    with db_manager.get_session() as session:
        tenant = session.query(Tenant).filter(Tenant.id == current_user["tenant_id"]).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant_data = {
            "id": tenant.id,
            "name": tenant.name,
            "code": tenant.code,
            "description": tenant.description,
            "logo": tenant.logo,
            "tagline": tenant.tagline,
            "address": tenant.address,
            "is_active": tenant.is_active
        }
    
    return BaseResponse(
        success=True,
        message="Tenant retrieved successfully",
        data=tenant_data
    )

@router.put("/tenant", response_model=BaseResponse)
async def update_tenant(tenant_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import Tenant
    
    # Validate business_type if provided
    if 'business_type' in tenant_data:
        business_type = tenant_data['business_type'].upper()
        if business_type not in ['TRADING', 'SERVICE', 'HYBRID']:
            raise HTTPException(status_code=400, detail="business_type must be TRADING, SERVICE, or HYBRID")
        tenant_data['business_type'] = business_type
    
    with db_manager.get_session() as session:
        tenant = session.query(Tenant).filter(Tenant.id == current_user["tenant_id"]).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Update tenant fields
        for key, value in tenant_data.items():
            if hasattr(tenant, key) and key != 'id' and key != 'code':  # Don't allow updating id or code
                setattr(tenant, key, value)
        
        session.commit()
        
        return BaseResponse(
            success=True,
            message="Tenant updated successfully"
        )

@router.get("/tenant-settings", response_model=BaseResponse)
async def get_tenant_settings(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import TenantSetting
    
    with db_manager.get_session() as session:
        settings = session.query(TenantSetting).filter(
            TenantSetting.tenant_id == current_user["tenant_id"]
        ).all()
        
        settings_data = [{
            "id": s.id,
            "setting": s.setting,
            "description": s.description,
            "value_type": s.value_type,
            "value": s.value
        } for s in settings]
    
    return BaseResponse(
        success=True,
        message="Tenant settings retrieved successfully",
        data=settings_data
    )

@router.put("/tenant-settings/{setting}", response_model=BaseResponse)
async def update_tenant_setting(setting: str, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import TenantSetting
    
    with db_manager.get_session() as session:
        tenant_setting = session.query(TenantSetting).filter(
            TenantSetting.tenant_id == current_user["tenant_id"],
            TenantSetting.setting == setting
        ).first()
        
        if not tenant_setting:
            raise HTTPException(status_code=404, detail="Setting not found")
        
        tenant_setting.value = data.get("value")
        tenant_setting.updated_by = current_user["username"]
        session.commit()
        
        return BaseResponse(
            success=True,
            message="Setting updated successfully"
        )

# Legal Entity endpoints
@router.get("/legal-entities", response_model=PaginatedResponse)
async def get_legal_entities(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import LegalEntity, User
    
    with db_manager.get_session() as session:
        query = session.query(LegalEntity).filter(LegalEntity.tenant_id == current_user["tenant_id"])
        
        if pagination.search:
            query = query.filter(or_(
                LegalEntity.name.ilike(f"%{pagination.search}%"),
                LegalEntity.code.ilike(f"%{pagination.search}%"),
                LegalEntity.registration_number.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        entities = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        entity_data = []
        for entity in entities:
            admin_user = session.query(User).filter(User.id == entity.admin_user_id).first() if entity.admin_user_id else None
            entity_data.append({
                "id": entity.id,
                "name": entity.name,
                "code": entity.code,
                "registration_number": entity.registration_number,
                "address": entity.address,
                "logo": entity.logo,
                "admin_user_id": entity.admin_user_id,
                "admin_user_name": f"{admin_user.first_name} {admin_user.last_name}" if admin_user else None,
                "is_active": entity.is_active
            })
    
    return PaginatedResponse(
        success=True,
        message="Legal entities retrieved successfully",
        data=entity_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/legal-entities", response_model=BaseResponse)
async def create_legal_entity(entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import LegalEntity
    
    with db_manager.get_session() as session:
        entity = LegalEntity(
            name=entity_data["name"],
            code=entity_data["code"],
            registration_number=entity_data.get("registration_number"),
            address=entity_data.get("address"),
            logo=entity_data.get("logo"),
            admin_user_id=entity_data.get("admin_user_id"),
            tenant_id=current_user["tenant_id"],
            is_active=entity_data.get("is_active", True),
            created_by=current_user["username"]
        )
        session.add(entity)
        session.commit()
        
        return BaseResponse(
            success=True,
            message="Legal entity created successfully",
            data={"id": entity.id}
        )

@router.put("/legal-entities/{entity_id}", response_model=BaseResponse)
async def update_legal_entity(entity_id: int, entity_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import LegalEntity
    
    with db_manager.get_session() as session:
        entity = session.query(LegalEntity).filter(
            LegalEntity.id == entity_id,
            LegalEntity.tenant_id == current_user["tenant_id"]
        ).first()
        
        if not entity:
            raise HTTPException(status_code=404, detail="Legal entity not found")
        
        for key, value in entity_data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'created_at', 'created_by']:
                setattr(entity, key, value)
        
        entity.updated_by = current_user["username"]
        session.commit()
        
        return BaseResponse(success=True, message="Legal entity updated successfully")

@router.delete("/legal-entities/{entity_id}", response_model=BaseResponse)
async def delete_legal_entity(entity_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import LegalEntity
    
    with db_manager.get_session() as session:
        entity = session.query(LegalEntity).filter(
            LegalEntity.id == entity_id,
            LegalEntity.tenant_id == current_user["tenant_id"]
        ).first()
        
        if not entity:
            raise HTTPException(status_code=404, detail="Legal entity not found")
        
        session.delete(entity)
        session.commit()
        
        return BaseResponse(success=True, message="Legal entity deleted successfully")

@router.get("/legal-entities/export-template")
async def export_legal_entities_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "code", "registration_number", "address", "logo", "admin_username", "is_active"])
    writer.writerow(["ABC Corp", "ABC001", "REG123456", "123 Main St", "logo.png", "admin_user", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=legal_entities_template.csv"}
    )

@router.post("/legal-entities/import", response_model=BaseResponse)
async def import_legal_entities(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import LegalEntity, User
    
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    imported_count = 0
    
    with db_manager.get_session() as session:
        for row in csv_data:
            try:
                # Skip header rows - check if name field contains header-like values
                name_value = row.get("name", "").strip().lower()
                if name_value in ["name", "entity name", "legal entity name", "company name"] or not name_value:
                    continue
                
                admin_user = None
                if row.get("admin_username"):
                    admin_user = session.query(User).filter(
                        User.username == row["admin_username"],
                        User.tenant_id == current_user["tenant_id"]
                    ).first()
                
                entity = LegalEntity(
                    name=row["name"],
                    code=row["code"],
                    registration_number=row.get("registration_number"),
                    address=row.get("address"),
                    logo=row.get("logo"),
                    admin_user_id=admin_user.id if admin_user else None,
                    tenant_id=current_user["tenant_id"],
                    is_active=row.get("is_active", "true").lower() == "true",
                    created_by=current_user["username"]
                )
                session.add(entity)
                imported_count += 1
            except Exception:
                continue
        
        session.commit()
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} legal entities successfully"
    )

# Financial Year endpoints
@router.get("/financial-years", response_model=PaginatedResponse)
async def get_financial_years(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import FiscalYear as FinancialYear
    
    with db_manager.get_session() as session:
        query = session.query(FinancialYear).filter(FinancialYear.tenant_id == current_user["tenant_id"])
        
        if pagination.search:
            query = query.filter(
                FinancialYear.name.ilike(f"%{pagination.search}%")
            )
        
        query = query.order_by(FinancialYear.start_date.desc())
        
        total = query.count()
        years = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        year_data = [{
            "id": year.id,
            "name": year.name,
            "start_date": year.start_date.isoformat() if year.start_date else None,
            "end_date": year.end_date.isoformat() if year.end_date else None,
            "is_active": year.is_active,
            "is_closed": year.is_closed
        } for year in years]
    
    return PaginatedResponse(
        success=True,
        message="Financial years retrieved successfully",
        data=year_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/financial-years", response_model=BaseResponse)
async def create_financial_year(year_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import FiscalYear as FinancialYear
    from datetime import datetime
    
    with db_manager.get_session() as session:
        # Check for duplicate name
        existing = session.query(FinancialYear).filter(
            FinancialYear.tenant_id == current_user["tenant_id"],
            FinancialYear.name == year_data["name"]
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Financial year name already exists")
        
        # If this is set as active, unset other active years
        if year_data.get("is_active"):
            session.query(FinancialYear).filter(
                FinancialYear.tenant_id == current_user["tenant_id"],
                FinancialYear.is_active == True
            ).update({"is_active": False})
        
        year = FinancialYear(
            name=year_data["name"],
            start_date=datetime.fromisoformat(year_data["start_date"]),
            end_date=datetime.fromisoformat(year_data["end_date"]),
            tenant_id=current_user["tenant_id"],
            is_active=year_data.get("is_active", True),
            created_by=current_user["username"]
        )
        session.add(year)
        session.commit()
        
        return BaseResponse(
            success=True,
            message="Financial year created successfully",
            data={"id": year.id}
        )

@router.put("/financial-years/{year_id}", response_model=BaseResponse)
async def update_financial_year(year_id: int, year_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import FiscalYear as FinancialYear
    from datetime import datetime
    
    with db_manager.get_session() as session:
        year = session.query(FinancialYear).filter(
            FinancialYear.id == year_id,
            FinancialYear.tenant_id == current_user["tenant_id"]
        ).first()
        
        if not year:
            raise HTTPException(status_code=404, detail="Financial year not found")
        
        # Check for duplicate name (excluding current record)
        if "name" in year_data:
            existing = session.query(FinancialYear).filter(
                FinancialYear.tenant_id == current_user["tenant_id"],
                FinancialYear.id != year_id,
                FinancialYear.name == year_data.get("name")
            ).first()
            
            if existing:
                raise HTTPException(status_code=400, detail="Financial year name already exists")
        
        # If this is set as active, unset other active years
        if year_data.get("is_active") and not year.is_active:
            session.query(FinancialYear).filter(
                FinancialYear.tenant_id == current_user["tenant_id"],
                FinancialYear.is_active == True
            ).update({"is_active": False})
        
        for key, value in year_data.items():
            if hasattr(year, key) and key not in ['id', 'tenant_id', 'created_at', 'created_by']:
                if key in ['start_date', 'end_date'] and value:
                    setattr(year, key, datetime.fromisoformat(value))
                else:
                    setattr(year, key, value)
        
        year.updated_by = current_user["username"]
        session.commit()
        
        return BaseResponse(success=True, message="Financial year updated successfully")

@router.delete("/financial-years/{year_id}", response_model=BaseResponse)
async def delete_financial_year(year_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import FiscalYear as FinancialYear
    
    with db_manager.get_session() as session:
        year = session.query(FinancialYear).filter(
            FinancialYear.id == year_id,
            FinancialYear.tenant_id == current_user["tenant_id"]
        ).first()
        
        if not year:
            raise HTTPException(status_code=404, detail="Financial year not found")
        
        session.delete(year)
        session.commit()
        
        return BaseResponse(success=True, message="Financial year deleted successfully")

@router.get("/financial-years/export-template")
async def export_financial_years_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "start_date", "end_date", "is_active"])
    writer.writerow(["FY 2024-25", "2024-04-01", "2025-03-31", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=financial_years_template.csv"}
    )

@router.post("/financial-years/import", response_model=BaseResponse)
async def import_financial_years(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import FiscalYear as FinancialYear
    from datetime import datetime
    
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    imported_count = 0
    
    with db_manager.get_session() as session:
        for row in csv_data:
            try:
                # If this is set as active, unset other active years
                if row.get("is_active", "false").lower() == "true":
                    session.query(FinancialYear).filter(
                        FinancialYear.tenant_id == current_user["tenant_id"],
                        FinancialYear.is_active == True
                    ).update({"is_active": False})
                
                year = FinancialYear(
                    name=row["name"],
                    start_date=datetime.fromisoformat(row["start_date"]),
                    end_date=datetime.fromisoformat(row["end_date"]),
                    tenant_id=current_user["tenant_id"],
                    is_active=row.get("is_active", "true").lower() == "true",
                    created_by=current_user["username"]
                )
                session.add(year)
                imported_count += 1
            except Exception:
                continue
        
        session.commit()
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} financial years successfully"
    )

# Agency endpoints
@router.get("/agencies", response_model=PaginatedResponse)
async def get_agencies(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.agency import Agency
    
    with db_manager.get_session() as session:
        query = session.query(Agency).filter(
            Agency.tenant_id == current_user['tenant_id'],
            Agency.is_delete == False
        )
        
        if pagination.search:
            query = query.filter(or_(
                Agency.name.ilike(f"%{pagination.search}%"),
                Agency.email.ilike(f"%{pagination.search}%"),
                Agency.phone.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        agencies = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        agency_data = [{
            "id": agency.id,
            "name": agency.name,
            "phone": agency.phone,
            "email": agency.email,
            "address": agency.address,
            "tax_id": agency.tax_id,
            "created_at": agency.created_at.isoformat() if agency.created_at else None,
            "created_by": agency.created_by,
            "modified_at": agency.modified_at.isoformat() if agency.modified_at else None,
            "modified_by": agency.modified_by
        } for agency in agencies]
    
    return PaginatedResponse(
        success=True,
        message="Agencies retrieved successfully",
        data=agency_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/agencies", response_model=BaseResponse)
async def create_agency(agency_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    agency_service = AgencyService()
    agency = agency_service.create(agency_data)
    return BaseResponse(
        success=True,
        message="Agency created successfully",
        data={"id": agency}
    )

@router.put("/agencies/{agency_id}", response_model=BaseResponse)
async def update_agency(agency_id: int, agency_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    agency_service = AgencyService()
    agency = agency_service.update(agency_id, agency_data)
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    
    return BaseResponse(success=True, message="Agency updated successfully")

@router.delete("/agencies/{agency_id}", response_model=BaseResponse)
async def delete_agency(agency_id: int, current_user: dict = Depends(get_current_user)):
    agency_service = AgencyService()
    success = agency_service.delete(agency_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agency not found")
    
    return BaseResponse(success=True, message="Agency deleted successfully")

@router.get("/agencies/export-template")
async def export_agencies_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "phone", "email", "address", "tax_id"])
    writer.writerow(["ABC Agency", "123-456-7890", "abc@agency.com", "123 Main St", "TAX001"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=agencies_template.csv"}
    )

@router.post("/agencies/import", response_model=BaseResponse)
async def import_agencies(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    agency_service = AgencyService()
    imported_count = 0
    
    for row in csv_data:
        try:
            agency_data = {
                "name": row["name"],
                "phone": row["phone"],
                "email": row.get("email", ""),
                "address": row.get("address", ""),
                "tax_id": row.get("tax_id", "")
            }
            
            agency_service.create(agency_data)
            imported_count += 1
        except Exception:
            continue
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} agencies successfully"
    )


# Role Menu Mapping endpoints
@router.get("/role-menu-mappings", response_model=PaginatedResponse)
async def get_role_menu_mappings(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import Role, RoleMenuMapping, MenuMaster
    
    with db_manager.get_session() as session:
        # Get only roles that have menu assignments
        query = session.query(Role).join(RoleMenuMapping).filter(
            Role.tenant_id == current_user["tenant_id"]
        ).distinct()
        
        if pagination.search:
            query = query.filter(or_(
                Role.name.ilike(f"%{pagination.search}%"),
                Role.description.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        roles = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        role_menu_data = []
        for role in roles:
            # Get assigned menus for this role
            role_mappings = session.query(RoleMenuMapping, MenuMaster).join(
                MenuMaster, RoleMenuMapping.menu_id == MenuMaster.id
            ).filter(
                RoleMenuMapping.role_id == role.id,
                RoleMenuMapping.tenant_id == current_user["tenant_id"]
            ).all()
            
            menu_names = [rm.MenuMaster.menu_name for rm in role_mappings[:2]]
            remaining = len(role_mappings) - 2 if len(role_mappings) > 2 else 0
            menus_display = ", ".join(menu_names)
            if remaining > 0:
                menus_display += f" +{remaining}"
            
            role_menu_data.append({
                "role_id": role.id,
                "role_name": role.name,
                "role_description": role.description,
                "menu_count": len(role_mappings),
                "menus": menus_display
            })
    
    return PaginatedResponse(
        success=True,
        message="Role menu mappings retrieved successfully",
        data=role_menu_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.get("/role-menu-mappings/{role_id}/menus", response_model=BaseResponse)
async def get_role_menus(role_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import MenuMaster, RoleMenuMapping, TenantModuleMapping, ModuleMaster
    
    with db_manager.get_session() as session:
        # Get active modules for tenant
        active_modules = session.query(ModuleMaster.module_code).join(
            TenantModuleMapping
        ).filter(
            TenantModuleMapping.tenant_id == current_user["tenant_id"],
            TenantModuleMapping.is_active == True
        ).all()
        
        module_codes = [m[0] for m in active_modules]
        
        # Get all menus for active modules, or all active menus if no modules mapped
        if module_codes:
            all_menus = session.query(MenuMaster).filter(
                MenuMaster.module_code.in_(module_codes),
                MenuMaster.is_active == True
            ).order_by(MenuMaster.sort_order).all()
        else:
            # Return all active menus so user can assign access
            # all_menus = session.query(MenuMaster).filter(
            #     MenuMaster.is_active == True
            # ).order_by(MenuMaster.sort_order).all()
            all_menus = []
        
        # Get existing role menu mappings
        role_mappings = session.query(RoleMenuMapping).filter(
            RoleMenuMapping.role_id == role_id,
            RoleMenuMapping.tenant_id == current_user["tenant_id"]
        ).all()
        
        mapping_dict = {rm.menu_id: rm for rm in role_mappings}
        
        menu_data = []
        for menu in all_menus:
            mapping = mapping_dict.get(menu.id)
            menu_data.append({
                "menu_id": menu.id,
                "menu_name": menu.menu_name,
                "menu_code": menu.menu_code,
                "module_code": menu.module_code,
                "parent_menu_id": menu.parent_menu_id,
                "icon": menu.icon,
                "route": menu.route,
                "is_assigned": mapping is not None,
                "can_create": mapping.can_create if mapping else False,
                "can_update": mapping.can_update if mapping else False,
                "can_delete": mapping.can_delete if mapping else False,
                "can_import": mapping.can_import if mapping else False,
                "can_export": mapping.can_export if mapping else False,
                "can_print": mapping.can_print if mapping else False
            })
        
        return BaseResponse(
            success=True,
            message="Role menus retrieved successfully",
            data=menu_data
        )

# Transaction Templates
@router.get("/transaction-templates", response_model=BaseResponse)
async def get_transaction_templates(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT id, name, code, transaction_type, description, is_active
            FROM transaction_templates
            WHERE tenant_id = :tenant_id
            ORDER BY name
        """), {"tenant_id": current_user["tenant_id"]})
        
        templates = [{
            "id": row[0],
            "name": row[1],
            "code": row[2],
            "transaction_type": row[3],
            "description": row[4],
            "is_active": row[5]
        } for row in result]
        
        return BaseResponse(
            success=True,
            message="Templates retrieved successfully",
            data=templates
        )

@router.get("/transaction-templates/{template_id}/rules", response_model=BaseResponse)
async def get_transaction_template_rules(template_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT ttr.id, ttr.line_number, ttr.account_type, ttr.account_id, ttr.entry_type, 
                   ttr.amount_source, ttr.narration, am.name as account_name
            FROM transaction_template_rules ttr
            LEFT JOIN account_masters am ON ttr.account_id = am.id
            WHERE ttr.template_id = :template_id AND ttr.tenant_id = :tenant_id
            ORDER BY ttr.line_number
        """), {"template_id": template_id, "tenant_id": current_user["tenant_id"]})
        
        rules = [{
            "id": row[0],
            "line_number": row[1],
            "account_type": row[2],
            "account_id": row[3],
            "entry_type": row[4],
            "amount_source": row[5],
            "narration": row[6],
            "account_name": row[7]
        } for row in result]
        
        return BaseResponse(
            success=True,
            message="Rules retrieved successfully",
            data=rules
        )

@router.put("/transaction-templates/{template_id}/rules", response_model=BaseResponse)
async def update_transaction_template_rules(template_id: int, rules: List[Dict[str, Any]], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        # Delete existing rules
        session.execute(text("""
            DELETE FROM transaction_template_rules
            WHERE template_id = :template_id AND tenant_id = :tenant_id
        """), {"template_id": template_id, "tenant_id": current_user["tenant_id"]})
        
        # Insert new rules
        for rule in rules:
            session.execute(text("""
                INSERT INTO transaction_template_rules
                (template_id, line_number, account_type, account_id, entry_type, amount_source, narration, tenant_id)
                VALUES (:template_id, :line_number, :account_type, :account_id, :entry_type, :amount_source, :narration, :tenant_id)
            """), {
                "template_id": template_id,
                "line_number": rule["line_number"],
                "account_type": rule.get("account_type"),
                "account_id": rule.get("account_id"),
                "entry_type": rule["entry_type"],
                "amount_source": rule["amount_source"],
                "narration": rule["narration"],
                "tenant_id": current_user["tenant_id"]
            })
        
        session.commit()
        
        return BaseResponse(
            success=True,
            message="Rules updated successfully"
        )

@router.get("/account-type-mappings", response_model=BaseResponse)
async def get_account_type_mappings(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT atm.id, atm.account_type, atm.account_id, am.name as account_name, am.code as account_code
            FROM account_type_mappings atm
            JOIN account_masters am ON atm.account_id = am.id
            WHERE atm.tenant_id = :tenant_id
            ORDER BY atm.account_type
        """), {"tenant_id": current_user["tenant_id"]})
        
        mappings = [{
            "id": row[0],
            "account_type": row[1],
            "account_id": row[2],
            "account_name": row[3],
            "account_code": row[4]
        } for row in result]
        
        return BaseResponse(
            success=True,
            message="Account type mappings retrieved successfully",
            data=mappings
        )

@router.put("/account-type-mappings/{account_type}", response_model=BaseResponse)
async def update_account_type_mapping(account_type: str, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        # Check if mapping exists
        existing = session.execute(text("""
            SELECT id FROM account_type_mappings
            WHERE account_type = :account_type AND tenant_id = :tenant_id
        """), {"account_type": account_type, "tenant_id": current_user["tenant_id"]}).fetchone()
        
        if existing:
            session.execute(text("""
                UPDATE account_type_mappings
                SET account_id = :account_id
                WHERE account_type = :account_type AND tenant_id = :tenant_id
            """), {
                "account_id": data["account_id"],
                "account_type": account_type,
                "tenant_id": current_user["tenant_id"]
            })
        else:
            session.execute(text("""
                INSERT INTO account_type_mappings (account_type, account_id, tenant_id, created_by)
                VALUES (:account_type, :account_id, :tenant_id, :created_by)
            """), {
                "account_type": account_type,
                "account_id": data["account_id"],
                "tenant_id": current_user["tenant_id"],
                "created_by": current_user["username"]
            })
        
        session.commit()
        
        return BaseResponse(
            success=True,
            message="Account type mapping updated successfully"
        )

@router.get("/accounts", response_model=BaseResponse)
async def get_accounts(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT am.id, am.name, am.code, ag.name as group_name
            FROM account_masters am
            JOIN account_groups ag ON am.account_group_id = ag.id
            WHERE am.tenant_id = :tenant_id AND am.is_active = true
            ORDER BY am.code
        """), {"tenant_id": current_user["tenant_id"]})
        
        accounts = [{
            "id": row[0],
            "name": row[1],
            "code": row[2],
            "group_name": row[3]
        } for row in result]
        
        return BaseResponse(
            success=True,
            message="Accounts retrieved successfully",
            data=accounts
        )

@router.put("/role-menu-mappings/{role_id}/menus", response_model=BaseResponse)
async def update_role_menus(role_id: int, menu_mappings: List[Dict[str, Any]], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import RoleMenuMapping
    
    with db_manager.get_session() as session:
        # Delete existing mappings for this role
        session.query(RoleMenuMapping).filter(
            RoleMenuMapping.role_id == role_id,
            RoleMenuMapping.tenant_id == current_user["tenant_id"]
        ).delete()
        
        # Create new mappings
        for mapping in menu_mappings:
            if mapping.get("is_assigned"):
                role_menu = RoleMenuMapping(
                    role_id=role_id,
                    menu_id=mapping["menu_id"],
                    can_create=mapping.get("can_create", False),
                    can_update=mapping.get("can_update", False),
                    can_delete=mapping.get("can_delete", False),
                    can_import=mapping.get("can_import", False),
                    can_export=mapping.get("can_export", False),
                    can_print=mapping.get("can_print", False),
                    tenant_id=current_user["tenant_id"],
                    created_by=current_user["username"]
                )
                session.add(role_menu)
        
        session.commit()
        
        return BaseResponse(
            success=True,
            message="Role menu mappings updated successfully"
        )
