"""
Add all missing menus that exist in React App.tsx
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
        print("Adding missing menus...")
        
        # Get parent IDs
        cur.execute("SELECT id, menu_code FROM menu_master WHERE parent_menu_id IS NULL")
        parents = {row['menu_code']: row['id'] for row in cur.fetchall()}
        
        # Missing menus to add
        new_menus = [
            # Admin
            ('Transaction Templates', 'TRANSACTION_TEMPLATES', 'ADMIN', 'ADMIN_MAIN', '/admin/transaction-templates', '📄', 9, False),
            ('Account Type Mappings', 'ACCOUNT_TYPE_MAPPINGS', 'ADMIN', 'ADMIN_MAIN', '/admin/account-type-mappings', '🔗', 10, False),
            ('Payment Terms', 'PAYMENT_TERMS', 'ADMIN', 'ADMIN_MAIN', '/admin/payment-terms', '💳', 11, False),
            ('Document Templates', 'DOCUMENT_TEMPLATES', 'ADMIN', 'ADMIN_MAIN', '/admin/document-templates', '📋', 12, False),
            ('Notifications', 'NOTIFICATIONS', 'ADMIN', 'ADMIN_MAIN', '/admin/notifications', '🔔', 13, False),
            ('Approval Workflows', 'APPROVAL_WORKFLOWS', 'ADMIN', 'ADMIN_MAIN', '/admin/approval-workflows', '✅', 14, False),
            ('Pending Approvals', 'PENDING_APPROVALS', 'ADMIN', 'ADMIN_MAIN', '/admin/pending-approvals', '⏳', 15, False),
            
            # Inventory
            ('Sales Invoice', 'SALES_INVOICE', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/sales-invoice', '🧾', 13, False),
            ('Purchase Invoice', 'PURCHASE_INVOICE', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/purchase-invoice', '📄', 14, False),
            ('Warehouses', 'WAREHOUSES', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/warehouses', '🏭', 15, False),
            ('Stock Transfer', 'STOCK_TRANSFER', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/stock-transfer', '🔄', 16, False),
            ('Stock by Location', 'STOCK_BY_LOCATION', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/stock-by-location', '📍', 17, False),
            ('Stock Valuation', 'STOCK_VALUATION', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/stock-valuation', '💰', 18, False),
            ('Stock Aging', 'STOCK_AGING', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/stock-aging', '⏰', 19, False),
            ('Order Commission', 'ORDER_COMMISSION', 'INVENTORY', 'INVENTORY_MAIN', '/inventory/order-commission', '💵', 20, False),
            
            # Account
            ('Account Groups', 'ACCOUNT_GROUPS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/account-groups', '📂', 7, False),
            ('Voucher Series', 'VOUCHER_SERIES', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/voucher-series', '🔢', 8, False),
            ('Cost Centers', 'COST_CENTERS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/cost-centers', '🏢', 9, False),
            ('Budgets', 'BUDGETS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/budgets', '💼', 10, False),
            ('Tax Management', 'TAX_MANAGEMENT', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/tax-management', '📊', 11, False),
            ('Currency Management', 'CURRENCY_MANAGEMENT', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/currency-management', '💱', 12, False),
            ('TDS Management', 'TDS_MANAGEMENT', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/tds-management', '📝', 13, False),
            ('Bank Reconciliation', 'BANK_RECONCILIATION', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/bank-reconciliation', '🏦', 14, False),
            ('Receipts', 'RECEIPTS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/receipts', '🧾', 15, False),
            ('Recurring Vouchers', 'RECURRING_VOUCHERS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/recurring-vouchers', '🔁', 16, False),
            ('Contra', 'CONTRA', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/contra', '↔️', 17, False),
            ('Credit Notes', 'CREDIT_NOTES', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/credit-notes', '📋', 18, False),
            ('Debit Notes', 'DEBIT_NOTES', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/debit-notes', '📄', 19, False),
            ('Day Book', 'DAY_BOOK', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/day-book', '📅', 20, False),
            ('Cash Book', 'CASH_BOOK', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/cash-book', '💵', 21, False),
            ('Bank Book', 'BANK_BOOK', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/bank-book', '🏦', 22, False),
            ('Outstanding Reports', 'OUTSTANDING_REPORTS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/outstanding-reports', '📊', 23, False),
            ('Comparative Reports', 'COMPARATIVE_REPORTS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/comparative-reports', '📈', 24, False),
            ('AR Aging', 'AR_AGING', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/reports/ar-aging', '⏰', 25, False),
            ('AP Aging', 'AP_AGING', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/reports/ap-aging', '⏱️', 26, False),
            ('Aging Analysis', 'AGING_ANALYSIS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/aging-analysis', '📊', 27, False),
            ('Audit Trail', 'AUDIT_TRAIL', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/audit-trail', '🔍', 28, False),
            ('Budget vs Actual', 'BUDGET_VS_ACTUAL', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/reports/budget-vs-actual', '📊', 29, False),
            ('GST Reports', 'GST_REPORTS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/gst-reports', '📋', 30, False),
            ('Fixed Assets', 'FIXED_ASSETS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/fixed-assets', '🏗️', 31, False),
            ('Asset Categories', 'ASSET_CATEGORIES', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/asset-categories', '📂', 32, False),
            ('Depreciation', 'DEPRECIATION', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/depreciation', '📉', 33, False),
            ('E-Invoice', 'EINVOICE', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/einvoice', '📧', 34, False),
            ('E-Way Bill', 'EWAY_BILL', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/eway-bill', '🚚', 35, False),
            ('GSTR-1', 'GSTR1', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/gstr1', '📄', 36, False),
            ('TDS Returns', 'TDS_RETURNS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/tds-returns', '📋', 37, False),
            ('Custom Reports', 'CUSTOM_REPORTS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/custom-reports', '📊', 38, False),
            ('Scheduled Reports', 'SCHEDULED_REPORTS', 'ACCOUNT', 'ACCOUNT_MAIN', '/account/scheduled-reports', '⏰', 39, False),
            
            # Clinic
            ('Billing Master', 'BILLING_MASTER', 'CLINIC', 'CLINIC_MAIN', '/clinic/billing-master', '💰', 8, False),
            ('Test Category', 'CLINIC_TEST_CATEGORY', 'CLINIC', 'CLINIC_MAIN', '/clinic/test-category', '📂', 9, False),
            ('Test Master', 'CLINIC_TEST_MASTER', 'CLINIC', 'CLINIC_MAIN', '/clinic/test-master', '🧪', 10, False),
            
            # Diagnostic
            ('Test Panel', 'TEST_PANEL', 'DIAGNOSTIC', 'DIAGNOSTIC_MAIN', '/diagnostic/test-panel', '📋', 5, False),
            ('Patient Management', 'DIAG_PATIENT_MGMT', 'DIAGNOSTIC', 'DIAGNOSTIC_MAIN', '/diagnostic/patient-management', '👥', 6, False),
            ('Doctor Management', 'DIAG_DOCTOR_MGMT', 'DIAGNOSTIC', 'DIAGNOSTIC_MAIN', '/diagnostic/doctor-management', '👨⚕️', 7, False),
            ('Order Commission', 'DIAG_ORDER_COMMISSION', 'DIAGNOSTIC', 'DIAGNOSTIC_MAIN', '/diagnostic/order-commission', '💵', 8, False),
        ]
        
        added = 0
        for name, code, module, parent_code, route, icon, sort, admin_only in new_menus:
            # Check if already exists
            cur.execute("SELECT id FROM menu_master WHERE menu_code = %s", (code,))
            if cur.fetchone():
                print(f"Skipped {code} (already exists)")
                continue
            
            parent_id = parents.get(parent_code)
            if not parent_id:
                print(f"Skipped {code} (parent {parent_code} not found)")
                continue
            
            cur.execute("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order, is_admin_only, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
            """, (name, code, module, parent_id, route, icon, sort, admin_only))
            added += 1
            print(f"Added {code}")
        
        # Grant Admin role access to new menus
        cur.execute("SELECT id, tenant_id FROM roles WHERE name = 'Admin'")
        admin_roles = cur.fetchall()
        
        cur.execute("SELECT id FROM menu_master")
        all_menu_ids = [row['id'] for row in cur.fetchall()]
        
        for role in admin_roles:
            for menu_id in all_menu_ids:
                cur.execute("""
                    INSERT INTO role_menu_mapping (role_id, menu_id, tenant_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (role_id, menu_id) DO NOTHING
                """, (role['id'], menu_id, role['tenant_id']))
        
        conn.commit()
        print(f"\nAdded {added} new menus")
        print("Granted Admin access to all menus")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run_migration()
