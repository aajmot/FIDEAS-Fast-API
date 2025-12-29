from typing import List, Dict, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.database.connection import db_manager
from modules.admin_module.models.entities import MenuMaster, RoleMenuMapping, User, UserRole, Role

class MenuService:
    
    @staticmethod
    def get_user_menus(user_id: int, tenant_id: int) -> List[Dict]:
        """Get all accessible menus for a user based on their roles"""
        with db_manager.get_session() as session:
            # Check if user is admin (has access to all menus)
            user = session.query(User).filter_by(id=user_id, tenant_id=tenant_id).first()
            if not user:
                return []
            
            # Check if user is tenant admin
            if user.is_tenant_admin:
                menus = session.query(MenuMaster).filter_by(is_active=True).order_by(
                    MenuMaster.sort_order
                ).all()
                menu_tree = MenuService._build_menu_tree(menus, user_id, tenant_id, session)
                return menu_tree
            
            # Get user roles with role names
            user_roles_query = session.query(UserRole, Role).join(Role).filter(
                UserRole.user_id == user_id,
                UserRole.tenant_id == tenant_id
            ).all()
            
            if not user_roles_query:
                print(f"DEBUG: No roles found for user {user_id}")
                return []
            
            # Check if any role is admin (case-insensitive)
            is_admin = False
            role_names = []
            for user_role, role in user_roles_query:
                role_names.append(role.name)
                if 'admin' in role.name.lower():
                    is_admin = True
            
            print(f"DEBUG: User {user_id} has roles: {role_names}")
            print(f"DEBUG: Is admin: {is_admin}")
            
            if is_admin:
                # Admin gets ALL menus including admin-only
                menus = session.query(MenuMaster).filter_by(is_active=True).order_by(
                    MenuMaster.sort_order
                ).all()
                print(f"DEBUG: Admin user - loaded {len(menus)} menus")
                
                # If no menus found, check total count
                total_menus = session.query(MenuMaster).count()
                print(f"DEBUG: Total menus in database: {total_menus}")
                
                if total_menus == 0:
                    print("DEBUG: No menus in database - inserting default menus")
                    MenuService._insert_default_menus(session)
                    menus = session.query(MenuMaster).filter_by(is_active=True).order_by(
                        MenuMaster.sort_order
                    ).all()
                    print(f"DEBUG: After insertion - loaded {len(menus)} menus")
                elif len(menus) < 10:  # Should have at least 10+ menus with submenus
                    print(f"DEBUG: Only {len(menus)} menus found, expected more - clearing and reinserting")
                    session.query(MenuMaster).delete()
                    session.commit()
                    MenuService._insert_default_menus(session)
                    menus = session.query(MenuMaster).filter_by(is_active=True).order_by(
                        MenuMaster.sort_order
                    ).all()
                    print(f"DEBUG: After reinsertion - loaded {len(menus)} menus")
            else:
                # Non-admin users: get union of all assigned menus (excluding admin-only)
                role_ids = [ur.role_id for ur, _ in user_roles_query]
                menu_mappings = session.query(RoleMenuMapping).filter(
                    and_(
                        RoleMenuMapping.role_id.in_(role_ids),
                        RoleMenuMapping.tenant_id == tenant_id
                    )
                ).all()
                
                if not menu_mappings:
                    print(f"DEBUG: No menu mappings found for roles: {role_ids}")
                    return []  # No menu access
                
                # Use set to ensure unique menu IDs (union of all role permissions)
                menu_ids = list(set([mapping.menu_id for mapping in menu_mappings]))
                
                menus = session.query(MenuMaster).filter(
                    and_(
                        MenuMaster.id.in_(menu_ids),
                        MenuMaster.is_active == True,
                        MenuMaster.is_admin_only == False
                    )
                ).order_by(MenuMaster.sort_order).all()
                print(f"DEBUG: Non-admin user - loaded {len(menus)} menus from {len(role_ids)} roles")
            
            # Debug: Print all menus found
            for menu in menus:
                print(f"DEBUG: Menu found - {menu.menu_name} (ID: {menu.id}, Parent: {menu.parent_menu_id})")
            
            menu_tree = MenuService._build_menu_tree(menus, user_id, tenant_id, session)
            print(f"DEBUG: Built menu tree with {len(menu_tree)} root items")
            for root_menu in menu_tree:
                print(f"DEBUG: Root menu - {root_menu['name']} has {len(root_menu['children'])} children")
            
            return menu_tree
    
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
    
    @staticmethod
    def _get_menu_permissions(menu_id: int, user_id: int, tenant_id: int, session: Session) -> Dict[str, bool]:
        """Get user permissions for a specific menu"""
        # Get user roles with role names
        user_roles_query = session.query(UserRole, Role).join(Role).filter(
            UserRole.user_id == user_id,
            UserRole.tenant_id == tenant_id
        ).all()
        
        if not user_roles_query:
            return {
                'can_create': False,
                'can_update': False,
                'can_delete': False,
                'can_import': False,
                'can_export': False,
                'can_print': False
            }
        
        # Check if any role is admin (case-insensitive)
        is_admin = any('admin' in role.name.lower() for _, role in user_roles_query)
        
        if is_admin:
            # Admin has ALL permissions for ALL menus
            return {
                'can_create': True,
                'can_update': True,
                'can_delete': True,
                'can_import': True,
                'can_export': True,
                'can_print': True
            }
        
        # Get permissions from role mappings using UNION (OR logic)
        role_ids = [ur.role_id for ur, _ in user_roles_query]
        mappings = session.query(RoleMenuMapping).filter(
            and_(
                RoleMenuMapping.role_id.in_(role_ids),
                RoleMenuMapping.menu_id == menu_id,
                RoleMenuMapping.tenant_id == tenant_id
            )
        ).all()
        
        # Union all permissions (if any role has permission, user gets it)
        permissions = {
            'can_create': any(m.can_create for m in mappings),
            'can_update': any(m.can_update for m in mappings),
            'can_delete': any(m.can_delete for m in mappings),
            'can_import': any(m.can_import for m in mappings),
            'can_export': any(m.can_export for m in mappings),
            'can_print': any(m.can_print for m in mappings)
        }
        
        return permissions
    
    @staticmethod
    def assign_menu_permissions(role_id: int, menu_id: int, permissions: Dict[str, bool], tenant_id: int, created_by: str) -> bool:
        """Assign menu permissions to a role"""
        try:
            with db_manager.get_session() as session:
                # Check if mapping already exists
                existing = session.query(RoleMenuMapping).filter_by(
                    role_id=role_id,
                    menu_id=menu_id
                ).first()
                
                if existing:
                    # Update existing mapping
                    existing.can_create = permissions.get('can_create', False)
                    existing.can_update = permissions.get('can_update', False)
                    existing.can_delete = permissions.get('can_delete', False)
                    existing.can_import = permissions.get('can_import', False)
                    existing.can_export = permissions.get('can_export', False)
                    existing.can_print = permissions.get('can_print', False)
                else:
                    # Create new mapping
                    mapping = RoleMenuMapping(
                        role_id=role_id,
                        menu_id=menu_id,
                        can_create=permissions.get('can_create', False),
                        can_update=permissions.get('can_update', False),
                        can_delete=permissions.get('can_delete', False),
                        can_import=permissions.get('can_import', False),
                        can_export=permissions.get('can_export', False),
                        can_print=permissions.get('can_print', False),
                        tenant_id=tenant_id,
                        created_by=created_by
                    )
                    session.add(mapping)
                
                session.commit()
                return True
        except Exception as e:
            print(f"Error assigning menu permissions: {e}")
            return False
    
    @staticmethod
    def get_all_menus() -> List[Dict]:
        """Get all menus for admin configuration"""
        with db_manager.get_session() as session:
            menus = session.query(MenuMaster).filter_by(is_active=True,is_deleted=False).order_by(
                MenuMaster.sort_order
            ).all()
            
            return MenuService._build_simple_menu_tree(menus)

    @staticmethod
    def get_all_active_menus() -> List[Dict]:
        """Return all active (and not-deleted if applicable) menus in the same
        tree format as `get_user_menus`.

        This uses `_build_menu_tree` so the returned structure contains the
        same fields (`id`, `name`, `code`, `module_code`, `icon`, `route`,
        `parent_menu_id`, `sort_order`, `children`) as the user-specific
        response.
        """
        with db_manager.get_session() as session:
            query = session.query(MenuMaster).filter(MenuMaster.is_active == True)

            # If the model has an `is_deleted` column, exclude deleted records
            if hasattr(MenuMaster, 'is_deleted'):
                query = query.filter(MenuMaster.is_deleted == False)

            menus = query.order_by(MenuMaster.sort_order).all()

            # `_build_menu_tree` expects user_id and tenant_id parameters but does
            # not use them for building the raw tree; pass zeros as placeholders.
            return MenuService._build_menu_tree(menus, user_id=0, tenant_id=0, session=session)
    
    @staticmethod
    def _build_simple_menu_tree(menus: List[MenuMaster]) -> List[Dict]:
        """Build simple menu tree without permissions"""
        menu_dict = {}
        root_menus = []
        
        for menu in menus:
            menu_data = {
                'id': menu.id,
                'name': menu.menu_name,
                'code': menu.menu_code,
                'module_code': menu.module_code,
                'icon': menu.icon,
                'route': menu.route,
                'sort_order': menu.sort_order,
                'is_admin_only': menu.is_admin_only,
                'children': []
            }
            
            menu_dict[menu.id] = menu_data
            
            if menu.parent_menu_id is None:
                root_menus.append(menu_data)
        
        # Build parent-child relationships
        for menu in menus:
            if menu.parent_menu_id and menu.parent_menu_id in menu_dict:
                parent = menu_dict[menu.parent_menu_id]
                child = menu_dict[menu.id]
                parent['children'].append(child)
        
        return sorted(root_menus, key=lambda x: x['sort_order'])
    
    @staticmethod
    def get_role_menu_permissions(role_id: int, tenant_id: int) -> Dict[int, Dict[str, bool]]:
        """Get all menu permissions for a specific role"""
        with db_manager.get_session() as session:
            mappings = session.query(RoleMenuMapping).filter_by(
                role_id=role_id,
                tenant_id=tenant_id
            ).all()
            
            permissions = {}
            for mapping in mappings:
                permissions[mapping.menu_id] = {
                    'can_create': mapping.can_create,
                    'can_update': mapping.can_update,
                    'can_delete': mapping.can_delete,
                    'can_import': mapping.can_import,
                    'can_export': mapping.can_export,
                    'can_print': mapping.can_print
                }
            
            return permissions
    
    @staticmethod
    def _insert_default_menus(session):
        """Insert default menus if none exist"""
        # Insert main menus
        main_menus = [
            MenuMaster(menu_name="Admin", menu_code="ADMIN_MAIN", module_code="ADMIN", icon="🔧", route="/admin", sort_order=1, is_admin_only=False),
            MenuMaster(menu_name="Inventory", menu_code="INVENTORY_MAIN", module_code="INVENTORY", icon="📦", route="/inventory", sort_order=2, is_admin_only=False),
            MenuMaster(menu_name="Accounts", menu_code="ACCOUNT_MAIN", module_code="ACCOUNT", icon="📊", route="/accounts", sort_order=3, is_admin_only=False),
            MenuMaster(menu_name="Clinic", menu_code="CLINIC_MAIN", module_code="CLINIC", icon="🏥", route="/clinic", sort_order=4, is_admin_only=False)
        ]
        
        for menu in main_menus:
            session.add(menu)
        session.flush()
        
        # Get all parent IDs
        admin_id = session.query(MenuMaster).filter_by(menu_code="ADMIN_MAIN").first().id
        inventory_id = session.query(MenuMaster).filter_by(menu_code="INVENTORY_MAIN").first().id
        account_id = session.query(MenuMaster).filter_by(menu_code="ACCOUNT_MAIN").first().id
        clinic_id = session.query(MenuMaster).filter_by(menu_code="CLINIC_MAIN").first().id
        
        # Insert all submenus
        submenus = [
            # Admin submenus
            MenuMaster(menu_name="User Management", menu_code="USER_MGMT", module_code="ADMIN", parent_menu_id=admin_id, icon="👥", route="/admin/users", sort_order=1, is_admin_only=False),
            MenuMaster(menu_name="Role Management", menu_code="ROLE_MGMT", module_code="ADMIN", parent_menu_id=admin_id, icon="🔑", route="/admin/roles", sort_order=2, is_admin_only=False),
            MenuMaster(menu_name="Menu Assignment", menu_code="MENU_ACCESS", module_code="ADMIN", parent_menu_id=admin_id, icon="🔒", route="/admin/menu-access", sort_order=3, is_admin_only=True),
            
            # Inventory submenus
            MenuMaster(menu_name="Product Management", menu_code="PRODUCT_MGMT", module_code="INVENTORY", parent_menu_id=inventory_id, icon="📦", route="/inventory/products", sort_order=1, is_admin_only=False),
            MenuMaster(menu_name="Category Management", menu_code="CATEGORY_MGMT", module_code="INVENTORY", parent_menu_id=inventory_id, icon="📂", route="/inventory/categories", sort_order=2, is_admin_only=False),
            MenuMaster(menu_name="Supplier Management", menu_code="SUPPLIER_MGMT", module_code="INVENTORY", parent_menu_id=inventory_id, icon="🚚", route="/inventory/suppliers", sort_order=3, is_admin_only=False),
            
            # Account submenus
            MenuMaster(menu_name="Chart of Accounts", menu_code="CHART_ACCOUNTS", module_code="ACCOUNT", parent_menu_id=account_id, icon="📈", route="/accounts/chart", sort_order=1, is_admin_only=False),
            MenuMaster(menu_name="Journal Entries", menu_code="JOURNAL_ENTRY", module_code="ACCOUNT", parent_menu_id=account_id, icon="📝", route="/accounts/journal", sort_order=2, is_admin_only=False),
            MenuMaster(menu_name="Customer Management", menu_code="CUSTOMER_MGMT", module_code="ACCOUNT", parent_menu_id=account_id, icon="👥", route="/accounts/customers", sort_order=3, is_admin_only=False),
            
            # Clinic submenus
            MenuMaster(menu_name="Patient Management", menu_code="PATIENT_MGMT", module_code="CLINIC", parent_menu_id=clinic_id, icon="🧑‍⚕️", route="/clinic/patients", sort_order=1, is_admin_only=False),
            MenuMaster(menu_name="Doctor Management", menu_code="DOCTOR_MGMT", module_code="CLINIC", parent_menu_id=clinic_id, icon="👨‍⚕️", route="/clinic/doctors", sort_order=2, is_admin_only=False),
            MenuMaster(menu_name="Appointments", menu_code="APPOINTMENT_MGMT", module_code="CLINIC", parent_menu_id=clinic_id, icon="📅", route="/clinic/appointments", sort_order=3, is_admin_only=False)
        ]
        
        for menu in submenus:
            session.add(menu)
        
        # Clear existing menus and insert comprehensive structure
        session.query(MenuMaster).delete()
        session.commit()
        
        # Re-insert main menus
        for menu in main_menus:
            session.add(menu)
        session.flush()
        
        # Get fresh IDs
        admin_id = session.query(MenuMaster).filter_by(menu_code="ADMIN_MAIN").first().id
        inventory_id = session.query(MenuMaster).filter_by(menu_code="INVENTORY_MAIN").first().id
        account_id = session.query(MenuMaster).filter_by(menu_code="ACCOUNT_MAIN").first().id
        clinic_id = session.query(MenuMaster).filter_by(menu_code="CLINIC_MAIN").first().id
        
        # Complete menu structure matching dashboard
        all_menus = [
            # Admin menus
            MenuMaster(menu_name="User Management", menu_code="USER_MGMT", module_code="ADMIN", parent_menu_id=admin_id, icon="👥", route="/admin/users", sort_order=1, is_admin_only=False),
            MenuMaster(menu_name="Role Management", menu_code="ROLE_MGMT", module_code="ADMIN", parent_menu_id=admin_id, icon="🔐", route="/admin/roles", sort_order=2, is_admin_only=False),
            MenuMaster(menu_name="User-Role Mapping", menu_code="USER_ROLE_MAPPING", module_code="ADMIN", parent_menu_id=admin_id, icon="🔗", route="/admin/user-roles", sort_order=3, is_admin_only=False),
            MenuMaster(menu_name="Menu Access", menu_code="MENU_ACCESS", module_code="ADMIN", parent_menu_id=admin_id, icon="🔒", route="/admin/menu-access", sort_order=4, is_admin_only=True),
            MenuMaster(menu_name="Tenant Update", menu_code="TENANT_UPDATE", module_code="ADMIN", parent_menu_id=admin_id, icon="🏢", route="/admin/tenant-update", sort_order=5, is_admin_only=True),
            MenuMaster(menu_name="Legal Entity Management", menu_code="LEGAL_ENTITY_MGMT", module_code="ADMIN", parent_menu_id=admin_id, icon="🏢", route="/admin/legal-entity", sort_order=6, is_admin_only=False),
            MenuMaster(menu_name="Financial Year", menu_code="FINANCIAL_YEAR", module_code="ADMIN", parent_menu_id=admin_id, icon="📅", route="/admin/financial-year", sort_order=7, is_admin_only=False),
            
            # Inventory Masters
            MenuMaster(menu_name="Unit Master", menu_code="UNIT_MASTER", module_code="INVENTORY", parent_menu_id=inventory_id, icon="📏", route="/inventory/units", sort_order=1, is_admin_only=False),
            MenuMaster(menu_name="Categories", menu_code="CATEGORY_MGMT", module_code="INVENTORY", parent_menu_id=inventory_id, icon="📂", route="/inventory/categories", sort_order=2, is_admin_only=False),
            MenuMaster(menu_name="Products", menu_code="PRODUCT_MGMT", module_code="INVENTORY", parent_menu_id=inventory_id, icon="🏷️", route="/inventory/products", sort_order=3, is_admin_only=False),
            MenuMaster(menu_name="Product Batches", menu_code="PRODUCT_BATCH_MGMT", module_code="INVENTORY", parent_menu_id=inventory_id, icon="📎", route="/inventory/product-batches", sort_order=4, is_admin_only=False),
            MenuMaster(menu_name="Customers", menu_code="INV_CUSTOMER_MGMT", module_code="INVENTORY", parent_menu_id=inventory_id, icon="👥", route="/inventory/customers", sort_order=5, is_admin_only=False),
            MenuMaster(menu_name="Suppliers", menu_code="SUPPLIER_MGMT", module_code="INVENTORY", parent_menu_id=inventory_id, icon="🏢", route="/inventory/suppliers", sort_order=6, is_admin_only=False),
            
            # Inventory Transactions
            MenuMaster(menu_name="Purchase Orders", menu_code="PURCHASE_ORDER", module_code="INVENTORY", parent_menu_id=inventory_id, icon="📋", route="/inventory/purchase-orders", sort_order=7, is_admin_only=False),
            MenuMaster(menu_name="Sales Orders", menu_code="SALES_ORDER", module_code="INVENTORY", parent_menu_id=inventory_id, icon="🛒", route="/inventory/sales-orders", sort_order=8, is_admin_only=False),
            MenuMaster(menu_name="Product Waste", menu_code="PRODUCT_WASTE", module_code="INVENTORY", parent_menu_id=inventory_id, icon="🗑️", route="/inventory/product-waste", sort_order=9, is_admin_only=False),
            
            # Inventory Stocks
            MenuMaster(menu_name="Stock Details", menu_code="STOCK_DETAILS", module_code="INVENTORY", parent_menu_id=inventory_id, icon="📊", route="/inventory/stock-details", sort_order=10, is_admin_only=False),
            MenuMaster(menu_name="Stock Meter", menu_code="STOCK_METER", module_code="INVENTORY", parent_menu_id=inventory_id, icon="⚠️", route="/inventory/stock-meter", sort_order=11, is_admin_only=False),
            MenuMaster(menu_name="Stock Tracking", menu_code="STOCK_TRACKING", module_code="INVENTORY", parent_menu_id=inventory_id, icon="📈", route="/inventory/stock-tracking", sort_order=12, is_admin_only=False),
            
            # Account menus
            MenuMaster(menu_name="Chart of Accounts", menu_code="CHART_ACCOUNTS", module_code="ACCOUNT", parent_menu_id=account_id, icon="📋", route="/accounts/chart", sort_order=1, is_admin_only=False),
            MenuMaster(menu_name="Ledger", menu_code="LEDGER", module_code="ACCOUNT", parent_menu_id=account_id, icon="📖", route="/accounts/ledger", sort_order=2, is_admin_only=False),
            MenuMaster(menu_name="Journal", menu_code="JOURNAL", module_code="ACCOUNT", parent_menu_id=account_id, icon="📝", route="/accounts/journal", sort_order=3, is_admin_only=False),
            MenuMaster(menu_name="Vouchers", menu_code="VOUCHERS", module_code="ACCOUNT", parent_menu_id=account_id, icon="🧾", route="/accounts/vouchers", sort_order=4, is_admin_only=False),
            MenuMaster(menu_name="Payments", menu_code="PAYMENTS", module_code="ACCOUNT", parent_menu_id=account_id, icon="💳", route="/accounts/payments", sort_order=5, is_admin_only=False),
            MenuMaster(menu_name="Reports", menu_code="REPORTS", module_code="ACCOUNT", parent_menu_id=account_id, icon="📊", route="/accounts/reports", sort_order=6, is_admin_only=False),
            
            # Clinic menus
            MenuMaster(menu_name="Patient Management", menu_code="PATIENT_MGMT", module_code="CLINIC", parent_menu_id=clinic_id, icon="👥", route="/clinic/patients", sort_order=1, is_admin_only=False),
            MenuMaster(menu_name="Doctor Management", menu_code="DOCTOR_MGMT", module_code="CLINIC", parent_menu_id=clinic_id, icon="👨⚕️", route="/clinic/doctors", sort_order=2, is_admin_only=False),
            MenuMaster(menu_name="Appointments", menu_code="APPOINTMENT_MGMT", module_code="CLINIC", parent_menu_id=clinic_id, icon="📅", route="/clinic/appointments", sort_order=3, is_admin_only=False),
            MenuMaster(menu_name="Medical Records", menu_code="MEDICAL_RECORDS", module_code="CLINIC", parent_menu_id=clinic_id, icon="📋", route="/clinic/records", sort_order=4, is_admin_only=False),
            MenuMaster(menu_name="Prescriptions", menu_code="PRESCRIPTION_MGMT", module_code="CLINIC", parent_menu_id=clinic_id, icon="💊", route="/clinic/prescriptions", sort_order=5, is_admin_only=False),
            MenuMaster(menu_name="Billing", menu_code="CLINIC_BILLING", module_code="CLINIC", parent_menu_id=clinic_id, icon="💰", route="/clinic/billing", sort_order=6, is_admin_only=False),
            MenuMaster(menu_name="Employees", menu_code="EMPLOYEE_MGMT", module_code="CLINIC", parent_menu_id=clinic_id, icon="👷", route="/clinic/employees", sort_order=7, is_admin_only=False)
        ]
        
        for menu in all_menus:
            session.add(menu)
        
        session.commit()
        print(f"DEBUG: Inserted {len(all_menus)} comprehensive menus successfully")