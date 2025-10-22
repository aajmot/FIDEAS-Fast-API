from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models.admin_models.menu_model import MenuMaster, RoleMenuMapping
from app.db.models.admin_models.role_model import Role

class MenuService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_menus(self, user_id: int, tenant_id: int):
        # Sample menu structure - in real implementation, this would be based on user roles
        sample_menus = [
            {
                "id": 1,
                "menu_name": "Dashboard",
                "menu_code": "DASHBOARD",
                "route": "/dashboard",
                "icon": "dashboard",
                "parent_menu_id": None,
                "sort_order": 1
            },
            {
                "id": 2,
                "menu_name": "Admin",
                "menu_code": "ADMIN",
                "route": "/admin",
                "icon": "admin_panel_settings",
                "parent_menu_id": None,
                "sort_order": 2
            },
            {
                "id": 3,
                "menu_name": "Users",
                "menu_code": "ADMIN_USERS",
                "route": "/admin/users",
                "icon": "people",
                "parent_menu_id": 2,
                "sort_order": 1
            },
            {
                "id": 4,
                "menu_name": "Roles",
                "menu_code": "ADMIN_ROLES",
                "route": "/admin/roles",
                "icon": "security",
                "parent_menu_id": 2,
                "sort_order": 2
            }
        ]
        return sample_menus
    
    def get_role_menu_mappings_paginated(self, tenant_id: int, search: str = None, offset: int = 0, limit: int = 10):
        query = self.db.query(Role).join(RoleMenuMapping).filter(
            Role.tenant_id == tenant_id
        ).distinct()
        
        if search:
            query = query.filter(or_(
                Role.name.ilike(f"%{search}%"),
                Role.description.ilike(f"%{search}%")
            ))
        
        total = query.count()
        roles = query.offset(offset).limit(limit).all()
        
        role_menu_data = []
        for role in roles:
            role_mappings = self.db.query(RoleMenuMapping, MenuMaster).join(
                MenuMaster, RoleMenuMapping.menu_id == MenuMaster.id
            ).filter(
                RoleMenuMapping.role_id == role.id,
                RoleMenuMapping.tenant_id == tenant_id
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
        
        return role_menu_data, total
    
    def get_role_menus(self, role_id: int, tenant_id: int):
        # Get all active menus (simplified - in real implementation would check tenant modules)
        all_menus = self.db.query(MenuMaster).filter(
            MenuMaster.is_active == True
        ).order_by(MenuMaster.sort_order).all()
        
        # Get existing role menu mappings
        role_mappings = self.db.query(RoleMenuMapping).filter(
            RoleMenuMapping.role_id == role_id,
            RoleMenuMapping.tenant_id == tenant_id
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
        
        return menu_data
    
    def update_role_menus(self, role_id: int, menu_mappings: List[Dict[str, Any]], tenant_id: int, created_by: str):
        # Delete existing mappings for this role
        self.db.query(RoleMenuMapping).filter(
            RoleMenuMapping.role_id == role_id,
            RoleMenuMapping.tenant_id == tenant_id
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
                    tenant_id=tenant_id,
                    created_by=created_by
                )
                self.db.add(role_menu)
        
        self.db.commit()