from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/role-menu-mappings", response_model=PaginatedResponse, operation_id="get_role_menu_mappings_list")
async def get_role_menu_mappings(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import Role, RoleMenuMapping, MenuMaster
    from sqlalchemy import or_

    with db_manager.get_session() as session:
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


@router.get("/role-menu-mappings/{role_id}/menus", response_model=BaseResponse, operation_id="get_role_menus_by_role_id")
async def get_role_menus(role_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import MenuMaster, RoleMenuMapping, TenantModuleMapping, ModuleMaster

    with db_manager.get_session() as session:
        active_modules = session.query(ModuleMaster.module_code).join(
            TenantModuleMapping
        ).filter(
            TenantModuleMapping.tenant_id == current_user["tenant_id"],
            TenantModuleMapping.is_active == True
        ).all()

        module_codes = [m[0] for m in active_modules]

        if module_codes:
            all_menus = session.query(MenuMaster).filter(
                MenuMaster.module_code.in_(module_codes),
                MenuMaster.is_active == True
            ).order_by(MenuMaster.sort_order).all()
        else:
            all_menus = []

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


@router.put("/role-menu-mappings/{role_id}/menus", response_model=BaseResponse, operation_id="update_role_menus_by_role_id")
async def update_role_menus(role_id: int, menu_mappings: List[Dict[str, Any]], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import RoleMenuMapping

    with db_manager.get_session() as session:
        session.query(RoleMenuMapping).filter(
            RoleMenuMapping.role_id == role_id,
            RoleMenuMapping.tenant_id == current_user["tenant_id"]
        ).delete()

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
