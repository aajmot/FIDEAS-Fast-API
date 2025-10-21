"""
Fix menu structure - restore to working state before any changes
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'fideas_enterprise_1'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'admin')
    )

def run_fix():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("Fixing menu structure...")
        
        # Delete all current menus
        cur.execute("DELETE FROM role_menu_mapping")
        cur.execute("DELETE FROM menu_master")
        
        # Insert correct menu structure - main modules should NOT have routes
        menus = [
            ('Admin', 'ADMIN_MAIN', 'ADMIN', None, None, '🔧', 1, False),
            ('Inventory', 'INVENTORY_MAIN', 'INVENTORY', None, None, '📦', 2, False),
            ('Account', 'ACCOUNT_MAIN', 'ACCOUNT', None, None, '📊', 3, False),
            ('Clinic', 'CLINIC_MAIN', 'CLINIC', None, None, '🏥', 4, False),
            ('Diagnostic', 'DIAGNOSTIC_MAIN', 'DIAGNOSTIC', None, None, '🔬', 5, False),
        ]
        
        menu_ids = {}
        for name, code, module, parent, route, icon, sort, admin_only in menus:
            cur.execute("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order, is_admin_only, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
                RETURNING id
            """, (name, code, module, parent, route, icon, sort, admin_only))
            menu_ids[code] = cur.fetchone()['id']
        
        # Submenus with proper routes
        submenus = [
            # Admin
            ('User Management', 'USER_MGMT', 'ADMIN', 'ADMIN_MAIN', '/admin/users', '👥', 1, False),
            ('Role Management', 'ROLE_MGMT', 'ADMIN', 'ADMIN_MAIN', '/admin/roles', '🔐', 2, False),
            ('User-Role Mapping', 'USER_ROLE_MAPPING', 'ADMIN', 'ADMIN_MAIN', '/admin/user-roles', '🔗', 3, False),
            ('Menu Access', 'MENU_ACCESS', 'ADMIN', 'ADMIN_MAIN', '/admin/menu-access', '🔒', 4, True),
            ('Tenant Update', 'TENANT_UPDATE', 'ADMIN', 'ADMIN_MAIN', '/admin/tenant-update', '🏢', 5, True),
            ('Legal Entity Management', 'LEGAL_ENTITY_MGMT', 'ADMIN', 'ADMIN_MAIN', '/admin/legal-entities', '🏢', 6, False),
            ('Financial Year', 'FINANCIAL_YEAR', 'ADMIN', 'ADMIN_MAIN', '/admin/financial-years', '📅', 7, False),
            ('Agency Management', 'AGENCY_MGMT', 'ADMIN', 'ADMIN_MAIN', '/admin/agencies', '🏪', 8, False),
            
            # Inventory
            ('Unit Master', 'UNIT_MASTER', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/units', '📏', 1, False),
            ('Categories', 'CATEGORY_MGMT', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/categories', '📂', 2, False),
            ('Products', 'PRODUCT_MGMT', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/products', '🏷️', 3, False),
            ('Product Batches', 'PRODUCT_BATCH_MGMT', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/product-batches', '📎', 4, False),
            ('Customers', 'INV_CUSTOMER_MGMT', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/customers', '👥', 5, False),
            ('Suppliers', 'SUPPLIER_MGMT', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/suppliers', '🏢', 6, False),
            ('Purchase Orders', 'PURCHASE_ORDER', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/purchase-orders', '📋', 7, False),
            ('Sales Orders', 'SALES_ORDER', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/sales-orders', '🛒', 8, False),
            ('Product Waste', 'PRODUCT_WASTE', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/product-waste', '🗑️', 9, False),
            ('Stock Details', 'STOCK_DETAILS', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/stock-details', '📊', 10, False),
            ('Stock Meter', 'STOCK_METER', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/stock-meter', '⚠️', 11, False),
            ('Stock Tracking', 'STOCK_TRACKING', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/stock-tracking', '📈', 12, False),
            
            # Account
            ('Chart of Accounts', 'CHART_ACCOUNTS', 'ACCOUNT', 'ACCOUNT_MAIN', '/accounting/accounts', '📋', 1, False),
            ('Ledger', 'LEDGER', 'ACCOUNT', 'ACCOUNT_MAIN', '/accounting/ledger', '📖', 2, False),
            ('Journal', 'JOURNAL', 'ACCOUNT', 'ACCOUNT_MAIN', '/accounting/journal', '📝', 3, False),
            ('Vouchers', 'VOUCHERS', 'ACCOUNT', 'ACCOUNT_MAIN', '/accounting/vouchers', '🧾', 4, False),
            ('Payments', 'PAYMENTS', 'ACCOUNT', 'ACCOUNT_MAIN', '/accounting/payments', '💳', 5, False),
            ('Reports', 'REPORTS', 'ACCOUNT', 'ACCOUNT_MAIN', '/accounting/reports', '📊', 6, False),
            
            # Clinic
            ('Patient Management', 'PATIENT_MGMT', 'CLINIC', 'CLINIC_MAIN', '/clinic/patients', '👥', 1, False),
            ('Doctor Management', 'DOCTOR_MGMT', 'CLINIC', 'CLINIC_MAIN', '/clinic/doctors', '👨⚕️', 2, False),
            ('Appointments', 'APPOINTMENT_MGMT', 'CLINIC', 'CLINIC_MAIN', '/clinic/appointments', '📅', 3, False),
            ('Medical Records', 'MEDICAL_RECORDS', 'CLINIC', 'CLINIC_MAIN', '/clinic/medical-records', '📋', 4, False),
            ('Prescriptions', 'PRESCRIPTION_MGMT', 'CLINIC', 'CLINIC_MAIN', '/clinic/prescriptions', '💊', 5, False),
            ('Billing', 'CLINIC_BILLING', 'CLINIC', 'CLINIC_MAIN', '/clinic/invoices', '💰', 6, False),
            ('Employees', 'EMPLOYEE_MGMT', 'CLINIC', 'CLINIC_MAIN', '/clinic/employees', '👷', 7, False),
            
            # Diagnostic
            ('Test Categories', 'TEST_CATEGORY_MGMT', 'DIAGNOSTIC', 'DIAGNOSTIC_MAIN', '/diagnostics/test-categories', '📂', 1, False),
            ('Test Master', 'TEST_MASTER', 'DIAGNOSTIC', 'DIAGNOSTIC_MAIN', '/diagnostics/tests', '🧪', 2, False),
            ('Test Orders', 'TEST_ORDER_MGMT', 'DIAGNOSTIC', 'DIAGNOSTIC_MAIN', '/diagnostics/test-orders', '📋', 3, False),
            ('Test Results', 'TEST_RESULT_MGMT', 'DIAGNOSTIC', 'DIAGNOSTIC_MAIN', '/diagnostics/test-results', '📊', 4, False),
        ]
        
        for name, code, module, parent_code, route, icon, sort, admin_only in submenus:
            parent_id = menu_ids.get(parent_code)
            cur.execute("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order, is_admin_only, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
                RETURNING id
            """, (name, code, module, parent_id, route, icon, sort, admin_only))
            menu_ids[code] = cur.fetchone()['id']
        
        # Grant Admin role access to all menus
        cur.execute("SELECT id, tenant_id FROM roles WHERE name = 'Admin'")
        admin_roles = cur.fetchall()
        
        for role in admin_roles:
            for code, menu_id in menu_ids.items():
                cur.execute("""
                    INSERT INTO role_menu_mapping (role_id, menu_id, tenant_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (role_id, menu_id) DO NOTHING
                """, (role['id'], menu_id, role['tenant_id']))
        
        conn.commit()
        print(f"Fix completed: {len(menu_ids)} menus created")
        print("Main modules: 5 (Admin, Inventory, Account, Clinic, Diagnostic)")
        print(f"Submenus: {len(submenus)}")
        
    except Exception as e:
        conn.rollback()
        print(f"Fix failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run_fix()
