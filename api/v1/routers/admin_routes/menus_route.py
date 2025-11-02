from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from sqlalchemy import or_
from modules.admin_module.services.menu_service import MenuService

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
