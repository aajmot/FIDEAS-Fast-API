"""
Migration 062: Menu Structure Modernization
- Consolidates duplicate Master/Transaction menus
- Creates 6 main modules: Dashboard, Administration, Inventory, Accounting, Clinic, Diagnostics
- Implements 2-3 level hierarchy with functional grouping
- Uses business-friendly names
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
        print("Starting menu restructure migration...")
        
        # Deactivate old menu structure
        cur.execute("UPDATE menu_master SET is_active = false")
        
        # New menu structure: (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
        menus = [
            # Level 1: Main Modules
            ('Dashboard', 'DASH', 'DASH', None, '/dashboard', 'dashboard', 1),
            ('Administration', 'ADMIN', 'ADMIN', None, None, 'settings', 2),
            ('Inventory', 'INV', 'INV', None, None, 'inventory', 3),
            ('Accounting', 'ACC', 'ACC', None, None, 'account_balance', 4),
            ('Clinic', 'CLINIC', 'CLINIC', None, None, 'local_hospital', 5),
            ('Diagnostics', 'DIAG', 'DIAG', None, None, 'biotech', 6),
        ]
        
        # Insert level 1 and get IDs
        menu_ids = {}
        for name, code, module, parent, route, icon, sort in menus:
            cur.execute("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                RETURNING id
            """, (name, code, module, parent, route, icon, sort))
            menu_ids[code] = cur.fetchone()['id']
        
        # Level 2 & 3 menus
        submenus = [
            # Administration submenus
            ('Users & Access', 'ADMIN_USERS', 'ADMIN', 'ADMIN', None, 'people', 1),
            ('User Management', 'ADMIN_USER_MGT', 'ADMIN', 'ADMIN_USERS', '/admin/users', 'person', 1),
            ('Role Management', 'ADMIN_ROLE_MGT', 'ADMIN', 'ADMIN_USERS', '/admin/roles', 'admin_panel_settings', 2),
            ('User-Role Mapping', 'ADMIN_USER_ROLE', 'ADMIN', 'ADMIN_USERS', '/admin/user-roles', 'link', 3),
            ('Menu Access Control', 'ADMIN_MENU_ACCESS', 'ADMIN', 'ADMIN_USERS', '/admin/menu-access', 'security', 4),
            
            ('Organization Setup', 'ADMIN_ORG', 'ADMIN', 'ADMIN', None, 'business', 2),
            ('Legal Entities', 'ADMIN_LEGAL', 'ADMIN', 'ADMIN_ORG', '/admin/legal-entities', 'corporate_fare', 1),
            ('Financial Years', 'ADMIN_FIN_YEAR', 'ADMIN', 'ADMIN_ORG', '/admin/financial-years', 'calendar_today', 2),
            ('Fiscal Years', 'ADMIN_FISCAL', 'ADMIN', 'ADMIN_ORG', '/admin/fiscal-years', 'date_range', 3),
            ('Agencies', 'ADMIN_AGENCY', 'ADMIN', 'ADMIN_ORG', '/admin/agencies', 'store', 4),
            
            ('System Configuration', 'ADMIN_CONFIG', 'ADMIN', 'ADMIN', None, 'tune', 3),
            ('Transaction Templates', 'ADMIN_TXN_TPL', 'ADMIN', 'ADMIN_CONFIG', '/admin/transaction-templates', 'description', 1),
            ('Account Type Mappings', 'ADMIN_ACC_MAP', 'ADMIN', 'ADMIN_CONFIG', '/admin/account-type-mappings', 'account_tree', 2),
            ('Payment Terms', 'ADMIN_PAY_TERMS', 'ADMIN', 'ADMIN_CONFIG', '/admin/payment-terms', 'payment', 3),
            ('Document Templates', 'ADMIN_DOC_TPL', 'ADMIN', 'ADMIN_CONFIG', '/admin/document-templates', 'article', 4),
            ('Notifications', 'ADMIN_NOTIF', 'ADMIN', 'ADMIN_CONFIG', '/admin/notifications', 'notifications', 5),
            
            ('Workflow & Approvals', 'ADMIN_WORKFLOW', 'ADMIN', 'ADMIN', None, 'approval', 4),
            ('Approval Workflows', 'ADMIN_WF_MGT', 'ADMIN', 'ADMIN_WORKFLOW', '/admin/approval-workflows', 'workflow', 1),
            ('Pending Approvals', 'ADMIN_PENDING', 'ADMIN', 'ADMIN_WORKFLOW', '/approvals/pending', 'pending_actions', 2),
            
            # Inventory submenus
            ('Master Data', 'INV_MASTER', 'INV', 'INV', None, 'folder', 1),
            ('Products', 'INV_PRODUCT', 'INV', 'INV_MASTER', '/inventory/products', 'inventory_2', 1),
            ('Categories', 'INV_CATEGORY', 'INV', 'INV_MASTER', '/inventory/categories', 'category', 2),
            ('Units of Measure', 'INV_UNIT', 'INV', 'INV_MASTER', '/inventory/units', 'straighten', 3),
            ('Customers', 'INV_CUSTOMER', 'INV', 'INV_MASTER', '/inventory/customers', 'person_outline', 4),
            ('Suppliers', 'INV_SUPPLIER', 'INV', 'INV_MASTER', '/inventory/suppliers', 'local_shipping', 5),
            
            ('Purchase', 'INV_PURCHASE', 'INV', 'INV', None, 'shopping_cart', 2),
            ('Purchase Orders', 'INV_PO', 'INV', 'INV_PURCHASE', '/inventory/purchase-orders', 'receipt_long', 1),
            ('Purchase Invoices', 'INV_PI', 'INV', 'INV_PURCHASE', '/inventory/purchase-invoices', 'receipt', 2),
            ('Supplier Payments', 'INV_SUPP_PAY', 'INV', 'INV_PURCHASE', '/inventory/supplier-payments', 'payments', 3),
            
            ('Sales', 'INV_SALES', 'INV', 'INV', None, 'point_of_sale', 3),
            ('Sales Orders', 'INV_SO', 'INV', 'INV_SALES', '/inventory/sales-orders', 'shopping_bag', 1),
            ('Sales Invoices', 'INV_SI', 'INV', 'INV_SALES', '/inventory/sales-invoices', 'description', 2),
            ('Customer Receipts', 'INV_CUST_REC', 'INV', 'INV_SALES', '/inventory/customer-receipts', 'account_balance_wallet', 3),
            
            ('Warehouse Operations', 'INV_WAREHOUSE', 'INV', 'INV', None, 'warehouse', 4),
            ('Warehouses', 'INV_WH', 'INV', 'INV_WAREHOUSE', '/inventory/warehouses', 'store', 1),
            ('Stock Transfers', 'INV_STOCK_TXF', 'INV', 'INV_WAREHOUSE', '/inventory/stock-transfers', 'swap_horiz', 2),
            ('Stock by Location', 'INV_STOCK_LOC', 'INV', 'INV_WAREHOUSE', '/inventory/stock-by-location', 'location_on', 3),
            ('Product Waste', 'INV_WASTE', 'INV', 'INV_WAREHOUSE', '/inventory/product-waste', 'delete_sweep', 4),
            
            ('Inventory Reports', 'INV_REPORTS', 'INV', 'INV', None, 'assessment', 5),
            ('Stock Details', 'INV_RPT_DETAIL', 'INV', 'INV_REPORTS', '/inventory/reports/stock-details', 'list_alt', 1),
            ('Stock Meter', 'INV_RPT_METER', 'INV', 'INV_REPORTS', '/inventory/reports/stock-meter', 'speed', 2),
            ('Stock Tracking', 'INV_RPT_TRACK', 'INV', 'INV_REPORTS', '/inventory/reports/stock-tracking', 'track_changes', 3),
            ('Stock Valuation', 'INV_RPT_VAL', 'INV', 'INV_REPORTS', '/inventory/reports/stock-valuation', 'attach_money', 4),
            ('Stock Aging', 'INV_RPT_AGING', 'INV', 'INV_REPORTS', '/inventory/reports/stock-aging', 'schedule', 5),
            ('Batch Management', 'INV_RPT_BATCH', 'INV', 'INV_REPORTS', '/inventory/reports/batch-management', 'batch_prediction', 6),
            
            # Accounting submenus
            ('Chart of Accounts', 'ACC_COA', 'ACC', 'ACC', None, 'account_tree', 1),
            ('Account Master', 'ACC_MASTER', 'ACC', 'ACC_COA', '/accounting/accounts', 'account_balance', 1),
            ('Account Groups', 'ACC_GROUP', 'ACC', 'ACC_COA', '/accounting/account-groups', 'folder_open', 2),
            ('Cost Centers', 'ACC_COST_CTR', 'ACC', 'ACC_COA', '/accounting/cost-centers', 'business_center', 3),
            
            ('Configuration', 'ACC_CONFIG', 'ACC', 'ACC', None, 'settings', 2),
            ('Voucher Series', 'ACC_VCH_SERIES', 'ACC', 'ACC_CONFIG', '/accounting/voucher-series', 'format_list_numbered', 1),
            ('Budgets', 'ACC_BUDGET', 'ACC', 'ACC_CONFIG', '/accounting/budgets', 'savings', 2),
            ('Tax Management', 'ACC_TAX', 'ACC', 'ACC_CONFIG', '/accounting/tax-management', 'calculate', 3),
            ('Currency Management', 'ACC_CURRENCY', 'ACC', 'ACC_CONFIG', '/accounting/currency-management', 'currency_exchange', 4),
            ('TDS Management', 'ACC_TDS', 'ACC', 'ACC_CONFIG', '/accounting/tds-management', 'request_quote', 5),
            
            ('Voucher Entry', 'ACC_VOUCHER', 'ACC', 'ACC', None, 'receipt_long', 3),
            ('Journal Entry', 'ACC_JOURNAL', 'ACC', 'ACC_VOUCHER', '/accounting/journal-entry', 'edit_note', 1),
            ('Payment Voucher', 'ACC_PAYMENT', 'ACC', 'ACC_VOUCHER', '/accounting/payment-voucher', 'payment', 2),
            ('Receipt Voucher', 'ACC_RECEIPT', 'ACC', 'ACC_VOUCHER', '/accounting/receipt-voucher', 'receipt', 3),
            ('Contra Voucher', 'ACC_CONTRA', 'ACC', 'ACC_VOUCHER', '/accounting/contra-voucher', 'swap_horiz', 4),
            ('Credit Note', 'ACC_CREDIT', 'ACC', 'ACC_VOUCHER', '/accounting/credit-note', 'note_add', 5),
            ('Debit Note', 'ACC_DEBIT', 'ACC', 'ACC_VOUCHER', '/accounting/debit-note', 'note', 6),
            ('Recurring Vouchers', 'ACC_RECURRING', 'ACC', 'ACC_VOUCHER', '/accounting/recurring-vouchers', 'repeat', 7),
            
            ('Fixed Assets', 'ACC_ASSETS', 'ACC', 'ACC', None, 'domain', 4),
            ('Asset Categories', 'ACC_ASSET_CAT', 'ACC', 'ACC_ASSETS', '/accounting/asset-categories', 'category', 1),
            ('Asset Register', 'ACC_ASSET_REG', 'ACC', 'ACC_ASSETS', '/accounting/fixed-assets', 'inventory', 2),
            ('Depreciation Schedule', 'ACC_DEPREC', 'ACC', 'ACC_ASSETS', '/accounting/depreciation-schedule', 'trending_down', 3),
            
            ('Books of Accounts', 'ACC_BOOKS', 'ACC', 'ACC', None, 'menu_book', 5),
            ('Ledger', 'ACC_LEDGER', 'ACC', 'ACC_BOOKS', '/accounting/ledger', 'book', 1),
            ('Day Book', 'ACC_DAYBOOK', 'ACC', 'ACC_BOOKS', '/accounting/day-book', 'today', 2),
            ('Cash Book', 'ACC_CASHBOOK', 'ACC', 'ACC_BOOKS', '/accounting/cash-book', 'account_balance_wallet', 3),
            ('Bank Book', 'ACC_BANKBOOK', 'ACC', 'ACC_BOOKS', '/accounting/bank-book', 'account_balance', 4),
            ('Bank Reconciliation', 'ACC_BANK_RECON', 'ACC', 'ACC_BOOKS', '/accounting/bank-reconciliation', 'done_all', 5),
            
            ('GST & Compliance', 'ACC_GST', 'ACC', 'ACC', None, 'gavel', 6),
            ('GST Reports', 'ACC_GST_RPT', 'ACC', 'ACC_GST', '/accounting/gst-reports', 'summarize', 1),
            ('E-Invoice', 'ACC_EINVOICE', 'ACC', 'ACC_GST', '/accounting/e-invoice', 'receipt_long', 2),
            ('E-Way Bill', 'ACC_EWAY', 'ACC', 'ACC_GST', '/accounting/e-way-bill', 'local_shipping', 3),
            ('GSTR-1 Filing', 'ACC_GSTR1', 'ACC', 'ACC_GST', '/accounting/gstr1-filing', 'upload_file', 4),
            ('TDS Returns', 'ACC_TDS_RET', 'ACC', 'ACC_GST', '/accounting/tds-returns', 'assignment_returned', 5),
            
            ('Financial Reports', 'ACC_FIN_RPT', 'ACC', 'ACC', None, 'bar_chart', 7),
            ('Trial Balance', 'ACC_TRIAL', 'ACC', 'ACC_FIN_RPT', '/accounting/trial-balance', 'balance', 1),
            ('Profit & Loss', 'ACC_PL', 'ACC', 'ACC_FIN_RPT', '/accounting/profit-loss', 'trending_up', 2),
            ('Balance Sheet', 'ACC_BS', 'ACC', 'ACC_FIN_RPT', '/accounting/balance-sheet', 'account_balance', 3),
            ('Cash Flow', 'ACC_CASHFLOW', 'ACC', 'ACC_FIN_RPT', '/accounting/cash-flow', 'waterfall_chart', 4),
            ('Outstanding Reports', 'ACC_OUTSTANDING', 'ACC', 'ACC_FIN_RPT', '/accounting/outstanding-reports', 'pending', 5),
            ('AR Aging Analysis', 'ACC_AR_AGING', 'ACC', 'ACC_FIN_RPT', '/accounting/ar-aging', 'schedule', 6),
            ('AP Aging Analysis', 'ACC_AP_AGING', 'ACC', 'ACC_FIN_RPT', '/accounting/ap-aging', 'schedule', 7),
            ('Comparative Reports', 'ACC_COMPARE', 'ACC', 'ACC_FIN_RPT', '/accounting/comparative-reports', 'compare', 8),
            ('Budget vs Actual', 'ACC_BVA', 'ACC', 'ACC_FIN_RPT', '/accounting/budget-vs-actual', 'compare_arrows', 9),
            ('Custom Reports', 'ACC_CUSTOM', 'ACC', 'ACC_FIN_RPT', '/accounting/custom-reports', 'dashboard_customize', 10),
            ('Scheduled Reports', 'ACC_SCHEDULED', 'ACC', 'ACC_FIN_RPT', '/accounting/scheduled-reports', 'schedule_send', 11),
            ('Audit Trail', 'ACC_AUDIT', 'ACC', 'ACC_FIN_RPT', '/accounting/audit-trail', 'history', 12),
            
            # Clinic submenus
            ('Patient Management', 'CLINIC_PATIENT', 'CLINIC', 'CLINIC', None, 'personal_injury', 1),
            ('Patient Registration', 'CLINIC_PAT_REG', 'CLINIC', 'CLINIC_PATIENT', '/clinic/patients', 'person_add', 1),
            ('Patient Records', 'CLINIC_PAT_REC', 'CLINIC', 'CLINIC_PATIENT', '/clinic/patient-records', 'folder_shared', 2),
            
            ('Doctor Management', 'CLINIC_DOCTOR', 'CLINIC', 'CLINIC', None, 'medical_services', 2),
            ('Doctor Master', 'CLINIC_DOC_MASTER', 'CLINIC', 'CLINIC_DOCTOR', '/clinic/doctors', 'badge', 1),
            ('Doctor Schedule', 'CLINIC_DOC_SCHED', 'CLINIC', 'CLINIC_DOCTOR', '/clinic/doctor-schedule', 'event', 2),
            
            ('Clinical Operations', 'CLINIC_OPS', 'CLINIC', 'CLINIC', None, 'local_hospital', 3),
            ('Appointments', 'CLINIC_APPT', 'CLINIC', 'CLINIC_OPS', '/clinic/appointments', 'event_available', 1),
            ('Medical Records', 'CLINIC_MED_REC', 'CLINIC', 'CLINIC_OPS', '/clinic/medical-records', 'medical_information', 2),
            ('Prescriptions', 'CLINIC_PRESC', 'CLINIC', 'CLINIC_OPS', '/clinic/prescriptions', 'medication', 3),
            ('Billing Master', 'CLINIC_BILL_MASTER', 'CLINIC', 'CLINIC_OPS', '/clinic/billing-master', 'receipt', 4),
            
            ('Billing', 'CLINIC_BILLING', 'CLINIC', 'CLINIC', None, 'payments', 4),
            ('Clinic Invoices', 'CLINIC_INVOICE', 'CLINIC', 'CLINIC_BILLING', '/clinic/invoices', 'description', 1),
            ('Payment Collection', 'CLINIC_PAY_COLL', 'CLINIC', 'CLINIC_BILLING', '/clinic/payment-collection', 'account_balance_wallet', 2),
            
            # Diagnostics submenus
            ('Test Configuration', 'DIAG_CONFIG', 'DIAG', 'DIAG', None, 'science', 1),
            ('Test Categories', 'DIAG_TEST_CAT', 'DIAG', 'DIAG_CONFIG', '/diagnostics/test-categories', 'category', 1),
            ('Test Master', 'DIAG_TEST_MASTER', 'DIAG', 'DIAG_CONFIG', '/diagnostics/tests', 'biotech', 2),
            ('Test Panels', 'DIAG_TEST_PANEL', 'DIAG', 'DIAG_CONFIG', '/diagnostics/test-panels', 'view_module', 3),
            
            ('Lab Operations', 'DIAG_LAB', 'DIAG', 'DIAG', None, 'science', 2),
            ('Test Orders', 'DIAG_TEST_ORDER', 'DIAG', 'DIAG_LAB', '/diagnostics/test-orders', 'assignment', 1),
            ('Test Results', 'DIAG_TEST_RESULT', 'DIAG', 'DIAG_LAB', '/diagnostics/test-results', 'assignment_turned_in', 2),
            ('Result Reports', 'DIAG_RESULT_RPT', 'DIAG', 'DIAG_LAB', '/diagnostics/result-reports', 'summarize', 3),
        ]
        
        # Insert submenus with parent resolution
        for name, code, module, parent_code, route, icon, sort in submenus:
            parent_id = menu_ids.get(parent_code)
            if not parent_id:
                # Find parent from already inserted submenus
                cur.execute("SELECT id FROM menu_master WHERE menu_code = %s", (parent_code,))
                result = cur.fetchone()
                if result:
                    parent_id = result['id']
            
            cur.execute("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                RETURNING id
            """, (name, code, module, parent_id, route, icon, sort))
            menu_ids[code] = cur.fetchone()['id']
        
        # Grant access to Admin role
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
        print(f"Menu restructure completed: {len(menu_ids)} menus created")
        print("Admin role granted access to all menus")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run_migration()
