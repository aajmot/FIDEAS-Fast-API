"""
Reorganize menus into 3-level hierarchy:
Level 1: Main Modules (Admin, Inventory, Account, Clinic, Diagnostic)
Level 2: Functional Groups (Masters, Transactions, Reports, Settings)
Level 3: Specific Features
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

def run_migration():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("Reorganizing menu hierarchy...")
        
        # Delete all menus
        cur.execute("DELETE FROM role_menu_mapping")
        cur.execute("DELETE FROM menu_master")
        
        # Level 1: Main Modules
        main_modules = [
            ('Admin', 'ADMIN', 'ADMIN', None, None, '🔧', 1),
            ('Inventory', 'INVENTORY', 'INVENTORY', None, None, '📦', 2),
            ('Account', 'ACCOUNT', 'ACCOUNT', None, None, '📊', 3),
            ('Clinic', 'CLINIC', 'CLINIC', None, None, '🏥', 4),
            ('Diagnostic', 'DIAGNOSTIC', 'DIAGNOSTIC', None, None, '🔬', 5),
        ]
        
        menu_ids = {}
        for name, code, module, parent, route, icon, sort in main_modules:
            cur.execute("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true) RETURNING id
            """, (name, code, module, parent, route, icon, sort))
            menu_ids[code] = cur.fetchone()['id']
        
        # Level 2: Functional Groups + Level 3: Features
        # Format: (name, code, module, parent_code, route, icon, sort, is_admin_only)
        menus = [
            # ADMIN MODULE
            ('Settings', 'ADMIN_SETTINGS', 'ADMIN', 'ADMIN', None, '⚙️', 1, False),
            ('User Management', 'USER_MGMT', 'ADMIN', 'ADMIN_SETTINGS', '/admin/user-management', '👥', 1, False),
            ('Role Management', 'ROLE_MGMT', 'ADMIN', 'ADMIN_SETTINGS', '/admin/role-management', '🔐', 2, False),
            ('User-Role Mapping', 'USER_ROLE_MAPPING', 'ADMIN', 'ADMIN_SETTINGS', '/admin/user-role-mapping', '🔗', 3, False),
            ('Menu Access', 'MENU_ACCESS', 'ADMIN', 'ADMIN_SETTINGS', '/admin/menu-access', '🔒', 4, True),
            ('Tenant Update', 'TENANT_UPDATE', 'ADMIN', 'ADMIN_SETTINGS', '/admin/tenant-update', '🏢', 5, True),
            
            ('Organization', 'ADMIN_ORG', 'ADMIN', 'ADMIN', None, '🏢', 2, False),
            ('Legal Entities', 'LEGAL_ENTITY_MGMT', 'ADMIN', 'ADMIN_ORG', '/admin/legal-entity', '🏢', 1, False),
            ('Financial Years', 'FINANCIAL_YEAR', 'ADMIN', 'ADMIN_ORG', '/admin/financial-years', '📅', 2, False),
            ('Agencies', 'AGENCY_MGMT', 'ADMIN', 'ADMIN_ORG', '/admin/agency-management', '🏪', 3, False),
            
            ('Configuration', 'ADMIN_CONFIG', 'ADMIN', 'ADMIN', None, '🔧', 3, False),
            ('Transaction Templates', 'TRANSACTION_TEMPLATES', 'ADMIN', 'ADMIN_CONFIG', '/admin/transaction-templates', '📄', 1, False),
            ('Account Type Mappings', 'ACCOUNT_TYPE_MAPPINGS', 'ADMIN', 'ADMIN_CONFIG', '/admin/account-type-mappings', '🔗', 2, False),
            ('Payment Terms', 'PAYMENT_TERMS', 'ADMIN', 'ADMIN_CONFIG', '/admin/payment-terms', '💳', 3, False),
            ('Document Templates', 'DOCUMENT_TEMPLATES', 'ADMIN', 'ADMIN_CONFIG', '/admin/document-templates', '📋', 4, False),
            ('Notifications', 'NOTIFICATIONS', 'ADMIN', 'ADMIN_CONFIG', '/admin/notifications', '🔔', 5, False),
            
            ('Approvals', 'ADMIN_APPROVALS', 'ADMIN', 'ADMIN', None, '✅', 4, False),
            ('Approval Workflows', 'APPROVAL_WORKFLOWS', 'ADMIN', 'ADMIN_APPROVALS', '/admin/approval-workflows', '✅', 1, False),
            ('Pending Approvals', 'PENDING_APPROVALS', 'ADMIN', 'ADMIN_APPROVALS', '/admin/pending-approvals', '⏳', 2, False),
            
            # INVENTORY MODULE
            ('Masters', 'INV_MASTERS', 'INVENTORY', 'INVENTORY', None, '📋', 1, False),
            ('Units', 'UNIT_MASTER', 'INVENTORY', 'INV_MASTERS', '/inventory/unit-management', '📏', 1, False),
            ('Categories', 'CATEGORY_MGMT', 'INVENTORY', 'INV_MASTERS', '/inventory/category-management', '📂', 2, False),
            ('Products', 'PRODUCT_MGMT', 'INVENTORY', 'INV_MASTERS', '/inventory/product-management', '🏷️', 3, False),
            ('Product Batches', 'PRODUCT_BATCH_MGMT', 'INVENTORY', 'INV_MASTERS', '/inventory/batch-management', '📎', 4, False),
            ('Customers', 'INV_CUSTOMER_MGMT', 'INVENTORY', 'INV_MASTERS', '/inventory/customer-management', '👥', 5, False),
            ('Suppliers', 'SUPPLIER_MGMT', 'INVENTORY', 'INV_MASTERS', '/inventory/supplier-management', '🏢', 6, False),
            ('Warehouses', 'WAREHOUSES', 'INVENTORY', 'INV_MASTERS', '/inventory/warehouses', '🏭', 7, False),
            
            ('Transactions', 'INV_TRANSACTIONS', 'INVENTORY', 'INVENTORY', None, '📝', 2, False),
            ('Purchase Orders', 'PURCHASE_ORDER', 'INVENTORY', 'INV_TRANSACTIONS', '/inventory/purchase-order', '📋', 1, False),
            ('Purchase Invoices', 'PURCHASE_INVOICE', 'INVENTORY', 'INV_TRANSACTIONS', '/inventory/purchase-invoice', '📄', 2, False),
            ('Sales Orders', 'SALES_ORDER', 'INVENTORY', 'INV_TRANSACTIONS', '/inventory/sales-order', '🛒', 3, False),
            ('Sales Invoices', 'SALES_INVOICE', 'INVENTORY', 'INV_TRANSACTIONS', '/inventory/sales-invoice', '🧾', 4, False),
            ('Stock Transfers', 'STOCK_TRANSFER', 'INVENTORY', 'INV_TRANSACTIONS', '/inventory/stock-transfer', '🔄', 5, False),
            ('Product Waste', 'PRODUCT_WASTE', 'INVENTORY', 'INV_TRANSACTIONS', '/inventory/product-waste', '🗑️', 6, False),
            ('Order Commission', 'ORDER_COMMISSION', 'INVENTORY', 'INV_TRANSACTIONS', '/inventory/order-commission', '💵', 7, False),
            
            ('Reports', 'INV_REPORTS', 'INVENTORY', 'INVENTORY', None, '📊', 3, False),
            ('Stock Details', 'STOCK_DETAILS', 'INVENTORY', 'INV_REPORTS', '/inventory/stock-details', '📊', 1, False),
            ('Stock by Location', 'STOCK_BY_LOCATION', 'INVENTORY', 'INV_REPORTS', '/inventory/stock-by-location', '📍', 2, False),
            ('Stock Meter', 'STOCK_METER', 'INVENTORY', 'INV_REPORTS', '/inventory/stock-meter', '⚠️', 3, False),
            ('Stock Tracking', 'STOCK_TRACKING', 'INVENTORY', 'INV_REPORTS', '/inventory/stock-tracking', '📈', 4, False),
            ('Stock Valuation', 'STOCK_VALUATION', 'INVENTORY', 'INV_REPORTS', '/inventory/stock-valuation', '💰', 5, False),
            ('Stock Aging', 'STOCK_AGING', 'INVENTORY', 'INV_REPORTS', '/inventory/stock-aging', '⏰', 6, False),
            
            # ACCOUNT MODULE
            ('Masters', 'ACC_MASTERS', 'ACCOUNT', 'ACCOUNT', None, '📋', 1, False),
            ('Chart of Accounts', 'CHART_ACCOUNTS', 'ACCOUNT', 'ACC_MASTERS', '/account/chart-accounts', '📋', 1, False),
            ('Account Groups', 'ACCOUNT_GROUPS', 'ACCOUNT', 'ACC_MASTERS', '/account/account-groups', '📂', 2, False),
            ('Cost Centers', 'COST_CENTERS', 'ACCOUNT', 'ACC_MASTERS', '/account/cost-centers', '🏢', 3, False),
            ('Voucher Series', 'VOUCHER_SERIES', 'ACCOUNT', 'ACC_MASTERS', '/account/voucher-series', '🔢', 4, False),
            
            ('Transactions', 'ACC_TRANSACTIONS', 'ACCOUNT', 'ACCOUNT', None, '📝', 2, False),
            ('Journal', 'JOURNAL', 'ACCOUNT', 'ACC_TRANSACTIONS', '/account/journal', '📝', 1, False),
            ('Vouchers', 'VOUCHERS', 'ACCOUNT', 'ACC_TRANSACTIONS', '/account/vouchers', '🧾', 2, False),
            ('Payments', 'PAYMENTS', 'ACCOUNT', 'ACC_TRANSACTIONS', '/account/payments', '💳', 3, False),
            ('Receipts', 'RECEIPTS', 'ACCOUNT', 'ACC_TRANSACTIONS', '/account/receipts', '🧾', 4, False),
            ('Contra', 'CONTRA', 'ACCOUNT', 'ACC_TRANSACTIONS', '/account/contra', '↔️', 5, False),
            ('Credit Notes', 'CREDIT_NOTES', 'ACCOUNT', 'ACC_TRANSACTIONS', '/account/credit-notes', '📋', 6, False),
            ('Debit Notes', 'DEBIT_NOTES', 'ACCOUNT', 'ACC_TRANSACTIONS', '/account/debit-notes', '📄', 7, False),
            ('Recurring Vouchers', 'RECURRING_VOUCHERS', 'ACCOUNT', 'ACC_TRANSACTIONS', '/account/recurring-vouchers', '🔁', 8, False),
            
            ('Books', 'ACC_BOOKS', 'ACCOUNT', 'ACCOUNT', None, '📖', 3, False),
            ('Ledger', 'LEDGER', 'ACCOUNT', 'ACC_BOOKS', '/account/ledger', '📖', 1, False),
            ('Day Book', 'DAY_BOOK', 'ACCOUNT', 'ACC_BOOKS', '/account/day-book', '📅', 2, False),
            ('Cash Book', 'CASH_BOOK', 'ACCOUNT', 'ACC_BOOKS', '/account/cash-book', '💵', 3, False),
            ('Bank Book', 'BANK_BOOK', 'ACCOUNT', 'ACC_BOOKS', '/account/bank-book', '🏦', 4, False),
            
            ('Fixed Assets', 'ACC_FIXED_ASSETS', 'ACCOUNT', 'ACCOUNT', None, '🏗️', 4, False),
            ('Asset Categories', 'ASSET_CATEGORIES', 'ACCOUNT', 'ACC_FIXED_ASSETS', '/account/asset-categories', '📂', 1, False),
            ('Fixed Assets', 'FIXED_ASSETS', 'ACCOUNT', 'ACC_FIXED_ASSETS', '/account/fixed-assets', '🏗️', 2, False),
            ('Depreciation', 'DEPRECIATION', 'ACCOUNT', 'ACC_FIXED_ASSETS', '/account/depreciation', '📉', 3, False),
            
            ('Reports', 'ACC_REPORTS', 'ACCOUNT', 'ACCOUNT', None, '📊', 5, False),
            ('Reports', 'REPORTS', 'ACCOUNT', 'ACC_REPORTS', '/account/reports', '📊', 1, False),
            ('Outstanding Reports', 'OUTSTANDING_REPORTS', 'ACCOUNT', 'ACC_REPORTS', '/account/outstanding-reports', '📊', 2, False),
            ('Comparative Reports', 'COMPARATIVE_REPORTS', 'ACCOUNT', 'ACC_REPORTS', '/account/comparative-reports', '📈', 3, False),
            ('AR Aging', 'AR_AGING', 'ACCOUNT', 'ACC_REPORTS', '/account/reports/ar-aging', '⏰', 4, False),
            ('AP Aging', 'AP_AGING', 'ACCOUNT', 'ACC_REPORTS', '/account/reports/ap-aging', '⏱️', 5, False),
            ('Aging Analysis', 'AGING_ANALYSIS', 'ACCOUNT', 'ACC_REPORTS', '/account/aging-analysis', '📊', 6, False),
            ('Budget vs Actual', 'BUDGET_VS_ACTUAL', 'ACCOUNT', 'ACC_REPORTS', '/account/reports/budget-vs-actual', '📊', 7, False),
            ('Audit Trail', 'AUDIT_TRAIL', 'ACCOUNT', 'ACC_REPORTS', '/account/audit-trail', '🔍', 8, False),
            ('Custom Reports', 'CUSTOM_REPORTS', 'ACCOUNT', 'ACC_REPORTS', '/account/custom-reports', '📊', 9, False),
            ('Scheduled Reports', 'SCHEDULED_REPORTS', 'ACCOUNT', 'ACC_REPORTS', '/account/scheduled-reports', '⏰', 10, False),
            
            ('GST & Compliance', 'ACC_GST', 'ACCOUNT', 'ACCOUNT', None, '📋', 6, False),
            ('GST Reports', 'GST_REPORTS', 'ACCOUNT', 'ACC_GST', '/account/gst-reports', '📋', 1, False),
            ('E-Invoice', 'EINVOICE', 'ACCOUNT', 'ACC_GST', '/account/einvoice', '📧', 2, False),
            ('E-Way Bill', 'EWAY_BILL', 'ACCOUNT', 'ACC_GST', '/account/eway-bill', '🚚', 3, False),
            ('GSTR-1', 'GSTR1', 'ACCOUNT', 'ACC_GST', '/account/gstr1', '📄', 4, False),
            ('TDS Returns', 'TDS_RETURNS', 'ACCOUNT', 'ACC_GST', '/account/tds-returns', '📋', 5, False),
            
            ('Settings', 'ACC_SETTINGS', 'ACCOUNT', 'ACCOUNT', None, '⚙️', 7, False),
            ('Budgets', 'BUDGETS', 'ACCOUNT', 'ACC_SETTINGS', '/account/budgets', '💼', 1, False),
            ('Tax Management', 'TAX_MANAGEMENT', 'ACCOUNT', 'ACC_SETTINGS', '/account/tax-management', '📊', 2, False),
            ('Currency Management', 'CURRENCY_MANAGEMENT', 'ACCOUNT', 'ACC_SETTINGS', '/account/currency-management', '💱', 3, False),
            ('TDS Management', 'TDS_MANAGEMENT', 'ACCOUNT', 'ACC_SETTINGS', '/account/tds-management', '📝', 4, False),
            ('Bank Reconciliation', 'BANK_RECONCILIATION', 'ACCOUNT', 'ACC_SETTINGS', '/account/bank-reconciliation', '🏦', 5, False),
            
            # CLINIC MODULE
            ('Masters', 'CLINIC_MASTERS', 'CLINIC', 'CLINIC', None, '📋', 1, False),
            ('Patients', 'PATIENT_MGMT', 'CLINIC', 'CLINIC_MASTERS', '/clinic/patient-management', '👥', 1, False),
            ('Doctors', 'DOCTOR_MGMT', 'CLINIC', 'CLINIC_MASTERS', '/clinic/doctor-management', '👨⚕️', 2, False),
            ('Employees', 'EMPLOYEE_MGMT', 'CLINIC', 'CLINIC_MASTERS', '/clinic/employees', '👷', 3, False),
            ('Billing Master', 'BILLING_MASTER', 'CLINIC', 'CLINIC_MASTERS', '/clinic/billing-master', '💰', 4, False),
            ('Test Categories', 'CLINIC_TEST_CATEGORY', 'CLINIC', 'CLINIC_MASTERS', '/clinic/test-category', '📂', 5, False),
            ('Test Master', 'CLINIC_TEST_MASTER', 'CLINIC', 'CLINIC_MASTERS', '/clinic/test-master', '🧪', 6, False),
            
            ('Transactions', 'CLINIC_TRANSACTIONS', 'CLINIC', 'CLINIC', None, '📝', 2, False),
            ('Appointments', 'APPOINTMENT_MGMT', 'CLINIC', 'CLINIC_TRANSACTIONS', '/clinic/appointments', '📅', 1, False),
            ('Medical Records', 'MEDICAL_RECORDS', 'CLINIC', 'CLINIC_TRANSACTIONS', '/clinic/medical-records', '📋', 2, False),
            ('Prescriptions', 'PRESCRIPTION_MGMT', 'CLINIC', 'CLINIC_TRANSACTIONS', '/clinic/prescriptions', '💊', 3, False),
            ('Billing', 'CLINIC_BILLING', 'CLINIC', 'CLINIC_TRANSACTIONS', '/clinic/billings', '💰', 4, False),
            
            # DIAGNOSTIC MODULE
            ('Masters', 'DIAG_MASTERS', 'DIAGNOSTIC', 'DIAGNOSTIC', None, '📋', 1, False),
            ('Test Categories', 'TEST_CATEGORY_MGMT', 'DIAGNOSTIC', 'DIAG_MASTERS', '/diagnostic/test-category', '📂', 1, False),
            ('Test Master', 'TEST_MASTER', 'DIAGNOSTIC', 'DIAG_MASTERS', '/diagnostic/test-master', '🧪', 2, False),
            ('Test Panels', 'TEST_PANEL', 'DIAGNOSTIC', 'DIAG_MASTERS', '/diagnostic/test-panel', '📋', 3, False),
            ('Patients', 'DIAG_PATIENT_MGMT', 'DIAGNOSTIC', 'DIAG_MASTERS', '/diagnostic/patient-management', '👥', 4, False),
            ('Doctors', 'DIAG_DOCTOR_MGMT', 'DIAGNOSTIC', 'DIAG_MASTERS', '/diagnostic/doctor-management', '👨⚕️', 5, False),
            
            ('Transactions', 'DIAG_TRANSACTIONS', 'DIAGNOSTIC', 'DIAGNOSTIC', None, '📝', 2, False),
            ('Test Orders', 'TEST_ORDER_MGMT', 'DIAGNOSTIC', 'DIAG_TRANSACTIONS', '/diagnostic/test-order', '📋', 1, False),
            ('Test Results', 'TEST_RESULT_MGMT', 'DIAGNOSTIC', 'DIAG_TRANSACTIONS', '/diagnostic/test-result', '📊', 2, False),
            ('Order Commission', 'DIAG_ORDER_COMMISSION', 'DIAGNOSTIC', 'DIAG_TRANSACTIONS', '/diagnostic/order-commission', '💵', 3, False),
        ]
        
        # Insert all menus
        for name, code, module, parent_code, route, icon, sort, admin_only in menus:
            parent_id = menu_ids.get(parent_code)
            if not parent_id:
                # Find parent from already inserted menus
                cur.execute("SELECT id FROM menu_master WHERE menu_code = %s", (parent_code,))
                result = cur.fetchone()
                if result:
                    parent_id = result['id']
            
            cur.execute("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order, is_admin_only, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true) RETURNING id
            """, (name, code, module, parent_id, route, icon, sort, admin_only))
            menu_ids[code] = cur.fetchone()['id']
        
        # Grant Admin access
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
        print(f"Reorganization completed: {len(menu_ids)} menus created")
        print("Structure: 5 main modules -> Functional groups -> Features")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run_migration()
