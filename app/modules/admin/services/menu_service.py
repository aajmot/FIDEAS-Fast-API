from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.db.models.admin_models.menu_model import MenuMaster, RoleMenuMapping
from app.db.models.admin_models.role_model import Role
from app.db.models.admin_models.user_model import User
from app.db.models.admin_models.user_role_model import UserRole

class MenuService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_menus(self, user_id: int, tenant_id: int):
        # Get user details
        user = self.db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_active == True
        ).first()
        
        if not user:
            return []
        
        # Check if user is tenant admin
        if user.is_tenant_admin:
            # Tenant admin gets all active menus
            menus = self.db.query(MenuMaster).filter(
                MenuMaster.is_active == True
            ).order_by(MenuMaster.sort_order).all()
        else:
            # Regular user gets menus based on assigned roles (union of all role permissions)
            menus = self.db.query(MenuMaster).join(
                RoleMenuMapping, MenuMaster.id == RoleMenuMapping.menu_id
            ).join(
                UserRole, RoleMenuMapping.role_id == UserRole.role_id
            ).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.tenant_id == tenant_id,
                    RoleMenuMapping.tenant_id == tenant_id,
                    MenuMaster.is_active == True
                )
            ).distinct().order_by(MenuMaster.sort_order).all()
        


        # Convert to dict format
        return MenuService._build_menu_tree(menus, user_id)
    
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

    @staticmethod
    def _build_menu_tree(menus: List[MenuMaster], user_id: int, tenant_id: int, session: Session) -> List[Dict]:
        """Build menu tree from database hierarchy"""
        menu_dict = {}
        
        # Convert to dict
        for menu in menus:
            menu_dict[menu.id] = {
                'id': menu.id,
                'name': menu.menu_name,
                'code': menu.menu_code,
                'module_code': menu.module_code,
                'icon': menu.icon,
                'route': menu.route,
                'parent_menu_id': menu.parent_menu_id,
                'sort_order': menu.sort_order,
                'children': []
            }
        
        # Build parent-child relationships
        for menu_data in menu_dict.values():
            if menu_data['parent_menu_id'] and menu_data['parent_menu_id'] in menu_dict:
                menu_dict[menu_data['parent_menu_id']]['children'].append(menu_data)
        
        # Get root menus and sort
        root_menus = [menu_data for menu_data in menu_dict.values() if not menu_data['parent_menu_id']]
        
        # Sort children recursively
        def sort_children(menu):
            menu['children'] = sorted(menu['children'], key=lambda x: x['sort_order'])
            for child in menu['children']:
                sort_children(child)
        
        for root in root_menus:
            sort_children(root)
        
        return sorted(root_menus, key=lambda x: x['sort_order'])
    