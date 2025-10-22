from typing import Dict, List, Optional
from modules.admin_module.services.menu_service import MenuService

class MenuUtils:
    """Utility class for menu-related operations in UI"""
    
    @staticmethod
    def get_user_menu_tree(user_id: int, tenant_id: int) -> List[Dict]:
        """Get hierarchical menu tree for user"""
        return MenuService.get_user_menus(user_id, tenant_id)
    
    @staticmethod
    def has_menu_permission(user_id: int, tenant_id: int, menu_code: str, permission: str) -> bool:
        """Check if user has specific permission for a menu"""
        menus = MenuService.get_user_menus(user_id, tenant_id)
        return MenuUtils._check_permission_recursive(menus, menu_code, permission)
    
    @staticmethod
    def _check_permission_recursive(menus: List[Dict], menu_code: str, permission: str) -> bool:
        """Recursively check permission in menu tree"""
        for menu in menus:
            if menu['code'] == menu_code:
                return menu['permissions'].get(permission, False)
            
            if menu['children']:
                if MenuUtils._check_permission_recursive(menu['children'], menu_code, permission):
                    return True
        
        return False
    
    @staticmethod
    def get_accessible_modules(user_id: int, tenant_id: int) -> List[str]:
        """Get list of module codes user has access to"""
        menus = MenuService.get_user_menus(user_id, tenant_id)
        modules = set()
        
        def extract_modules(menu_list):
            for menu in menu_list:
                modules.add(menu['module_code'])
                if menu['children']:
                    extract_modules(menu['children'])
        
        extract_modules(menus)
        return list(modules)
    
    @staticmethod
    def can_access_route(user_id: int, tenant_id: int, route: str) -> bool:
        """Check if user can access a specific route"""
        menus = MenuService.get_user_menus(user_id, tenant_id)
        return MenuUtils._check_route_access(menus, route)
    
    @staticmethod
    def _check_route_access(menus: List[Dict], route: str) -> bool:
        """Recursively check route access in menu tree"""
        for menu in menus:
            if menu['route'] == route:
                return True
            
            if menu['children']:
                if MenuUtils._check_route_access(menu['children'], route):
                    return True
        
        return False
    
    @staticmethod
    def get_menu_breadcrumb(user_id: int, tenant_id: int, menu_code: str) -> List[Dict]:
        """Get breadcrumb path for a menu"""
        menus = MenuService.get_user_menus(user_id, tenant_id)
        breadcrumb = []
        
        def find_breadcrumb(menu_list, target_code, path):
            for menu in menu_list:
                current_path = path + [{'name': menu['name'], 'code': menu['code'], 'route': menu['route']}]
                
                if menu['code'] == target_code:
                    breadcrumb.extend(current_path)
                    return True
                
                if menu['children']:
                    if find_breadcrumb(menu['children'], target_code, current_path):
                        return True
            
            return False
        
        find_breadcrumb(menus, menu_code, [])
        return breadcrumb