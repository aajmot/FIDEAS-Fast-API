#!/usr/bin/env python3
"""
Default Data Setup Migration
Inserts all required default data for FIDEAS application
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def insert_default_data():
    """Insert all required default data for all modules"""
    print("Inserting default data...")
    
    try:
        with db_manager.get_session() as session:
            # Insert module master data
            from modules.admin_module.models.entities import ModuleMaster
            existing_modules = session.query(ModuleMaster).count()
            if existing_modules == 0:
                modules = [
                    ModuleMaster(module_name="Admin Module", module_code="ADMIN", description="User and tenant management", is_mandatory=True),
                    ModuleMaster(module_name="Inventory Module", module_code="INVENTORY", description="Stock and inventory management"),
                    ModuleMaster(module_name="Account Module", module_code="ACCOUNT", description="Financial accounting"),
                    ModuleMaster(module_name="Clinic Module", module_code="CLINIC", description="Healthcare management"),
                    ModuleMaster(module_name="Diagnostic Module", module_code="DIAGNOSTIC", description="Diagnostic lab management")
                ]
                for module in modules:
                    session.add(module)
                session.commit()
                print("[OK] Module master data inserted")

            # Insert inventory units
            from modules.inventory_module.models.entities import Unit
            existing_units = session.query(Unit).count()
            if existing_units == 0:
                units = [
                    Unit(name='Piece', symbol='pcs'),
                    Unit(name='Box', symbol='box'),
                    Unit(name='Bottle', symbol='btl'),
                    Unit(name='Kilogram', symbol='kg'),
                    Unit(name='Gram', symbol='g'),
                    Unit(name='Liter', symbol='l'),
                    Unit(name='Milliliter', symbol='ml')
                ]
                for unit in units:
                    session.add(unit)
                session.commit()
                print("[OK] Inventory units inserted")

            # Insert menu data with proper parent-child structure
            insert_menu_data(session)
            
    except Exception as e:
        print(f"[ERROR] Error inserting default data: {str(e)}")
        raise

def insert_menu_data(session):
    """Insert menu data with proper module-menu-submenu hierarchy matching MainLayout.tsx"""
    from modules.admin_module.models.entities import MenuMaster, RoleMenuMapping
    
    existing_menus = session.query(MenuMaster).count()
    if existing_menus > 0:
        print("[INFO] Deleting existing menu data...")
        session.query(RoleMenuMapping).delete()
        session.query(MenuMaster).delete()
        session.commit()
        print("[OK] Existing menu data deleted")
    
    # Admin Module - Master
    admin_master = MenuMaster(menu_name="Master", menu_code="ADMIN_MASTER", module_code="ADMIN", icon="📋", sort_order=1)
    session.add(admin_master)
    session.flush()
    
    admin_master_items = [
        MenuMaster(menu_name="User Management", menu_code="USER_MGMT", module_code="ADMIN", parent_menu_id=admin_master.id, icon="👥", route="/admin/users", sort_order=1),
        MenuMaster(menu_name="Role Management", menu_code="ROLE_MGMT", module_code="ADMIN", parent_menu_id=admin_master.id, icon="🔐", route="/admin/roles", sort_order=2),
        MenuMaster(menu_name="Agency", menu_code="AGENCY_MGMT", module_code="ADMIN", parent_menu_id=admin_master.id, icon="🏢", route="/admin/agencies", sort_order=3),
        MenuMaster(menu_name="Legal Entity", menu_code="LEGAL_ENTITY", module_code="ADMIN", parent_menu_id=admin_master.id, icon="⚖️", route="/admin/legal-entities", sort_order=4),
        MenuMaster(menu_name="Financial Year", menu_code="FINANCIAL_YEAR", module_code="ADMIN", parent_menu_id=admin_master.id, icon="📅", route="/admin/financial-years", sort_order=5)
    ]
    for item in admin_master_items:
        session.add(item)
    
    # Admin Module - Transaction
    admin_trans = MenuMaster(menu_name="Transaction", menu_code="ADMIN_TRANSACTION", module_code="ADMIN", icon="💼", sort_order=2)
    session.add(admin_trans)
    session.flush()
    
    admin_trans_items = [
        MenuMaster(menu_name="User-Role Mapping", menu_code="USER_ROLE_MAPPING", module_code="ADMIN", parent_menu_id=admin_trans.id, icon="🔗", route="/admin/user-role-mappings", sort_order=1),
        MenuMaster(menu_name="Menu Access", menu_code="MENU_ACCESS", module_code="ADMIN", parent_menu_id=admin_trans.id, icon="📋", route="/admin/menu-access", sort_order=2),
        MenuMaster(menu_name="Tenant Update", menu_code="TENANT_UPDATE", module_code="ADMIN", parent_menu_id=admin_trans.id, icon="🏢", route="/admin/tenant", sort_order=3)
    ]
    for item in admin_trans_items:
        session.add(item)
    
    # Inventory Module - Master
    inv_master = MenuMaster(menu_name="Master", menu_code="INVENTORY_MASTER", module_code="INVENTORY", icon="📋", sort_order=1)
    session.add(inv_master)
    session.flush()
    
    inv_master_items = [
        MenuMaster(menu_name="Unit", menu_code="UNIT_MGMT", module_code="INVENTORY", parent_menu_id=inv_master.id, icon="📏", route="/inventory/units", sort_order=1),
        MenuMaster(menu_name="Category", menu_code="CATEGORY_MGMT", module_code="INVENTORY", parent_menu_id=inv_master.id, icon="📂", route="/inventory/categories", sort_order=2),
        MenuMaster(menu_name="Product", menu_code="PRODUCT_MGMT", module_code="INVENTORY", parent_menu_id=inv_master.id, icon="🛍️", route="/inventory/products", sort_order=3),
        MenuMaster(menu_name="Customer", menu_code="CUSTOMER_MGMT", module_code="INVENTORY", parent_menu_id=inv_master.id, icon="👤", route="/inventory/customers", sort_order=4),
        MenuMaster(menu_name="Supplier", menu_code="SUPPLIER_MGMT", module_code="INVENTORY", parent_menu_id=inv_master.id, icon="🏭", route="/inventory/suppliers", sort_order=5)
    ]
    for item in inv_master_items:
        session.add(item)
    
    # Inventory Module - Transaction
    inv_trans = MenuMaster(menu_name="Transaction", menu_code="INVENTORY_TRANSACTION", module_code="INVENTORY", icon="💼", sort_order=2)
    session.add(inv_trans)
    session.flush()
    
    inv_trans_items = [
        MenuMaster(menu_name="Purchase Order", menu_code="PURCHASE_ORDER", module_code="INVENTORY", parent_menu_id=inv_trans.id, icon="🛒", route="/inventory/purchase-orders", sort_order=1),
        MenuMaster(menu_name="Sales Order", menu_code="SALES_ORDER", module_code="INVENTORY", parent_menu_id=inv_trans.id, icon="🛍️", route="/inventory/sales-orders", sort_order=2),
        MenuMaster(menu_name="Product Waste", menu_code="PRODUCT_WASTE", module_code="INVENTORY", parent_menu_id=inv_trans.id, icon="🗑️", route="/inventory/product-wastes", sort_order=3)
    ]
    for item in inv_trans_items:
        session.add(item)
    
    # Inventory Module - Stock
    inv_stock = MenuMaster(menu_name="Stock", menu_code="INVENTORY_STOCK", module_code="INVENTORY", icon="📊", sort_order=3)
    session.add(inv_stock)
    session.flush()
    
    inv_stock_items = [
        MenuMaster(menu_name="Stock Details", menu_code="STOCK_DETAILS", module_code="INVENTORY", parent_menu_id=inv_stock.id, icon="📋", route="/inventory/stock-details", sort_order=1),
        MenuMaster(menu_name="Stock Meter", menu_code="STOCK_METER", module_code="INVENTORY", parent_menu_id=inv_stock.id, icon="📈", route="/inventory/stock-meter", sort_order=2),
        MenuMaster(menu_name="Stock Tracking", menu_code="STOCK_TRACKING", module_code="INVENTORY", parent_menu_id=inv_stock.id, icon="🔍", route="/inventory/stock-tracking", sort_order=3)
    ]
    for item in inv_stock_items:
        session.add(item)
    
    # Account Module - Master
    account_master = MenuMaster(menu_name="Master", menu_code="ACCOUNT_MASTER", module_code="ACCOUNT", icon="📋", sort_order=1)
    session.add(account_master)
    session.flush()
    
    account_master_items = [
        MenuMaster(menu_name="Chart Of Accounts", menu_code="CHART_ACCOUNTS", module_code="ACCOUNT", parent_menu_id=account_master.id, icon="📊", route="/account/chart-accounts", sort_order=1),
        MenuMaster(menu_name="Account Groups", menu_code="ACCOUNT_GROUPS", module_code="ACCOUNT", parent_menu_id=account_master.id, icon="📁", route="/account/account-groups", sort_order=2),
        MenuMaster(menu_name="Voucher Series", menu_code="VOUCHER_SERIES", module_code="ACCOUNT", parent_menu_id=account_master.id, icon="🔢", route="/account/voucher-series", sort_order=3),
        MenuMaster(menu_name="Fiscal Year", menu_code="FISCAL_YEAR_ACC", module_code="ACCOUNT", parent_menu_id=account_master.id, icon="📅", route="/admin/financial-year", sort_order=4),
        MenuMaster(menu_name="Cost Centers", menu_code="COST_CENTERS", module_code="ACCOUNT", parent_menu_id=account_master.id, icon="🏢", route="/account/cost-centers", sort_order=5),
        MenuMaster(menu_name="Budgets", menu_code="BUDGETS", module_code="ACCOUNT", parent_menu_id=account_master.id, icon="💼", route="/account/budgets", sort_order=6),
        MenuMaster(menu_name="Tax Management", menu_code="TAX_MANAGEMENT", module_code="ACCOUNT", parent_menu_id=account_master.id, icon="💰", route="/account/tax-management", sort_order=7),
        MenuMaster(menu_name="Currency Management", menu_code="CURRENCY_MANAGEMENT", module_code="ACCOUNT", parent_menu_id=account_master.id, icon="💱", route="/account/currency-management", sort_order=8)
    ]
    for item in account_master_items:
        session.add(item)
    
    # Account Module - Transaction
    account_trans = MenuMaster(menu_name="Transaction", menu_code="ACCOUNT_TRANSACTION", module_code="ACCOUNT", icon="💼", sort_order=2)
    session.add(account_trans)
    session.flush()
    
    account_trans_items = [
        MenuMaster(menu_name="Journal Entry", menu_code="JOURNAL", module_code="ACCOUNT", parent_menu_id=account_trans.id, icon="📝", route="/account/journal", sort_order=1),
        MenuMaster(menu_name="Vouchers", menu_code="VOUCHERS", module_code="ACCOUNT", parent_menu_id=account_trans.id, icon="📜", route="/account/vouchers", sort_order=2),
        MenuMaster(menu_name="Payment", menu_code="PAYMENTS", module_code="ACCOUNT", parent_menu_id=account_trans.id, icon="💸", route="/account/payments", sort_order=3),
        MenuMaster(menu_name="Receipt", menu_code="RECEIPTS", module_code="ACCOUNT", parent_menu_id=account_trans.id, icon="💰", route="/account/receipts", sort_order=4),
        MenuMaster(menu_name="Recurring Vouchers", menu_code="RECURRING_VOUCHERS", module_code="ACCOUNT", parent_menu_id=account_trans.id, icon="🔄", route="/account/recurring-vouchers", sort_order=5)
    ]
    for item in account_trans_items:
        session.add(item)
    
    # Account Module - Books
    account_books = MenuMaster(menu_name="Books", menu_code="ACCOUNT_BOOKS", module_code="ACCOUNT", icon="📚", sort_order=3)
    session.add(account_books)
    session.flush()
    
    account_books_items = [
        MenuMaster(menu_name="Ledger", menu_code="LEDGER", module_code="ACCOUNT", parent_menu_id=account_books.id, icon="📖", route="/account/ledger", sort_order=1),
        MenuMaster(menu_name="Day Book", menu_code="DAY_BOOK", module_code="ACCOUNT", parent_menu_id=account_books.id, icon="📅", route="/account/day-book", sort_order=2),
        MenuMaster(menu_name="Bank Book", menu_code="BANK_BOOK", module_code="ACCOUNT", parent_menu_id=account_books.id, icon="🏦", route="/account/bank-book", sort_order=3),
        MenuMaster(menu_name="Bank Reconciliation", menu_code="BANK_RECONCILIATION", module_code="ACCOUNT", parent_menu_id=account_books.id, icon="✅", route="/account/bank-reconciliation", sort_order=4)
    ]
    for item in account_books_items:
        session.add(item)
    
    # Account Module - Reports
    account_reports = MenuMaster(menu_name="Reports", menu_code="ACCOUNT_REPORTS", module_code="ACCOUNT", icon="📈", sort_order=4)
    session.add(account_reports)
    session.flush()
    
    account_reports_items = [
        MenuMaster(menu_name="Trial Balance", menu_code="TRIAL_BALANCE", module_code="ACCOUNT", parent_menu_id=account_reports.id, icon="⚖️", route="/account/reports?tab=trial-balance", sort_order=1),
        MenuMaster(menu_name="Profit & Loss", menu_code="PROFIT_LOSS", module_code="ACCOUNT", parent_menu_id=account_reports.id, icon="💹", route="/account/reports?tab=profit-loss", sort_order=2),
        MenuMaster(menu_name="Balance Sheet", menu_code="BALANCE_SHEET", module_code="ACCOUNT", parent_menu_id=account_reports.id, icon="📊", route="/account/reports?tab=balance-sheet", sort_order=3),
        MenuMaster(menu_name="Cash Flow", menu_code="CASH_FLOW", module_code="ACCOUNT", parent_menu_id=account_reports.id, icon="💵", route="/account/reports?tab=cash-flow", sort_order=4),
        MenuMaster(menu_name="Outstanding Reports", menu_code="OUTSTANDING_REPORTS", module_code="ACCOUNT", parent_menu_id=account_reports.id, icon="📋", route="/account/outstanding-reports", sort_order=5),
        MenuMaster(menu_name="Comparative Reports", menu_code="COMPARATIVE_REPORTS", module_code="ACCOUNT", parent_menu_id=account_reports.id, icon="📊", route="/account/comparative-reports", sort_order=6)
    ]
    for item in account_reports_items:
        session.add(item)
    
    # Clinic Module - Master
    clinic_master = MenuMaster(menu_name="Master", menu_code="CLINIC_MASTER", module_code="CLINIC", icon="📋", sort_order=1)
    session.add(clinic_master)
    session.flush()
    
    clinic_master_items = [
        MenuMaster(menu_name="Patient", menu_code="PATIENT_MGMT", module_code="CLINIC", parent_menu_id=clinic_master.id, icon="👤", route="/clinic/patients", sort_order=1),
        MenuMaster(menu_name="Doctor", menu_code="DOCTOR_MGMT", module_code="CLINIC", parent_menu_id=clinic_master.id, icon="👨⚕️", route="/clinic/doctors", sort_order=2),
        MenuMaster(menu_name="Billing Master", menu_code="BILLING_MASTER", module_code="CLINIC", parent_menu_id=clinic_master.id, icon="📋", route="/clinic/billing-masters", sort_order=3),
        MenuMaster(menu_name="Test Category", menu_code="TEST_CATEGORY", module_code="CLINIC", parent_menu_id=clinic_master.id, icon="🏷️", route="/clinic/test-categories", sort_order=4),
        MenuMaster(menu_name="Test Master", menu_code="TEST_MASTER", module_code="CLINIC", parent_menu_id=clinic_master.id, icon="🧪", route="/clinic/tests", sort_order=5)
    ]
    for item in clinic_master_items:
        session.add(item)
    
    # Clinic Module - Transaction
    clinic_trans = MenuMaster(menu_name="Transaction", menu_code="CLINIC_TRANSACTION", module_code="CLINIC", icon="💼", sort_order=2)
    session.add(clinic_trans)
    session.flush()
    
    clinic_trans_items = [
        MenuMaster(menu_name="Appointment", menu_code="APPOINTMENTS", module_code="CLINIC", parent_menu_id=clinic_trans.id, icon="📅", route="/clinic/appointments", sort_order=1),
        MenuMaster(menu_name="Medical Record", menu_code="MEDICAL_RECORDS", module_code="CLINIC", parent_menu_id=clinic_trans.id, icon="📄", route="/clinic/medical-records", sort_order=2),
        MenuMaster(menu_name="Prescription", menu_code="PRESCRIPTIONS", module_code="CLINIC", parent_menu_id=clinic_trans.id, icon="💊", route="/clinic/prescriptions", sort_order=3),
        MenuMaster(menu_name="Billing", menu_code="BILLINGS", module_code="CLINIC", parent_menu_id=clinic_trans.id, icon="💵", route="/clinic/invoices", sort_order=4)
    ]
    for item in clinic_trans_items:
        session.add(item)
    
    # Diagnostic Module - Master
    diagnostic_master = MenuMaster(menu_name="Master", menu_code="DIAGNOSTIC_MASTER", module_code="DIAGNOSTIC", icon="📋", sort_order=1)
    session.add(diagnostic_master)
    session.flush()
    
    diagnostic_master_items = [
        MenuMaster(menu_name="Patient", menu_code="DIAGNOSTIC_PATIENT_MGMT", module_code="DIAGNOSTIC", parent_menu_id=diagnostic_master.id, icon="👤", route="/diagnostic/patients", sort_order=1),
        MenuMaster(menu_name="Doctor", menu_code="DIAGNOSTIC_DOCTOR_MGMT", module_code="DIAGNOSTIC", parent_menu_id=diagnostic_master.id, icon="👨⚕️", route="/diagnostic/doctors", sort_order=2),
        MenuMaster(menu_name="Test Category", menu_code="DIAGNOSTIC_TEST_CATEGORY", module_code="DIAGNOSTIC", parent_menu_id=diagnostic_master.id, icon="🏷️", route="/diagnostic/test-categories", sort_order=3),
        MenuMaster(menu_name="Test Master", menu_code="DIAGNOSTIC_TEST_MASTER", module_code="DIAGNOSTIC", parent_menu_id=diagnostic_master.id, icon="🧪", route="/diagnostic/tests", sort_order=4),
        MenuMaster(menu_name="Test Panel", menu_code="TEST_PANEL", module_code="DIAGNOSTIC", parent_menu_id=diagnostic_master.id, icon="📊", route="/diagnostic/test-panels", sort_order=5)
    ]
    for item in diagnostic_master_items:
        session.add(item)
    
    # Diagnostic Module - Transaction
    diagnostic_trans = MenuMaster(menu_name="Transaction", menu_code="DIAGNOSTIC_TRANSACTION", module_code="DIAGNOSTIC", icon="💼", sort_order=2)
    session.add(diagnostic_trans)
    session.flush()
    
    diagnostic_trans_items = [
        MenuMaster(menu_name="Test Order", menu_code="TEST_ORDER", module_code="DIAGNOSTIC", parent_menu_id=diagnostic_trans.id, icon="📋", route="/diagnostic/test-orders", sort_order=1),
        MenuMaster(menu_name="Test Result", menu_code="TEST_RESULT", module_code="DIAGNOSTIC", parent_menu_id=diagnostic_trans.id, icon="📊", route="/diagnostic/test-results", sort_order=2)
    ]
    for item in diagnostic_trans_items:
        session.add(item)
    
    session.commit()
    print("[OK] Menu data with module-menu-submenu structure inserted")

def insert_account_master_data(tenant_id):
    """Insert default account groups and accounts for a specific tenant"""
    print(f"Inserting account master data for tenant {tenant_id}...")
    
    try:
        with db_manager.get_session() as session:
            # Insert account groups
            account_groups_data = [
                ('ASSETS', 'AST', None, 'ASSET'),
                ('Current Assets', 'CA', 1, 'ASSET'),
                ('Fixed Assets', 'FA', 1, 'ASSET'),
                ('LIABILITIES', 'LIB', None, 'LIABILITY'),
                ('Current Liabilities', 'CL', 4, 'LIABILITY'),
                ('Long Term Liabilities', 'LTL', 4, 'LIABILITY'),
                ('EQUITY', 'EQT', None, 'EQUITY'),
                ('INCOME', 'INC', None, 'INCOME'),
                ('EXPENSES', 'EXP', None, 'EXPENSE'),
            ]
            
            group_ids = {}
            for name, code, parent_id, acc_type in account_groups_data:
                # Check if group exists
                existing = session.execute(text(
                    "SELECT id FROM account_groups WHERE code = :code AND tenant_id = :tenant_id"
                ), {"code": code, "tenant_id": tenant_id}).fetchone()
                
                if not existing:
                    result = session.execute(text(
                        "INSERT INTO account_groups (name, code, parent_id, account_type, tenant_id) VALUES (:name, :code, :parent_id, :acc_type, :tenant_id) RETURNING id"
                    ), {"name": name, "code": code, "parent_id": parent_id, "acc_type": acc_type, "tenant_id": tenant_id})
                    group_ids[code] = result.fetchone()[0]
                else:
                    group_ids[code] = existing[0]
            
            # Insert default accounts
            accounts_data = [
                ('Cash in Hand', 'CASH001', 'CA'),
                ('Bank Account', 'BANK001', 'CA'),
                ('Accounts Receivable', 'AR001', 'CA'),
                ('Inventory', 'INV001', 'CA'),
                ('Accounts Payable', 'AP001', 'CL'),
                ('Sales Tax Payable', 'STP001', 'CL'),
                ('Owner Equity', 'OE001', 'EQT'),
                ('Sales Revenue', 'SR001', 'INC'),
                ('Purchase Expense', 'PE001', 'EXP'),
                ('Operating Expenses', 'OE002', 'EXP'),
            ]
            
            for name, code, group_code in accounts_data:
                # Check if account exists
                existing = session.execute(text(
                    "SELECT id FROM account_masters WHERE code = :code AND tenant_id = :tenant_id"
                ), {"code": code, "tenant_id": tenant_id}).fetchone()
                
                if not existing:
                    session.execute(text(
                        "INSERT INTO account_masters (name, code, account_group_id, tenant_id, created_by) VALUES (:name, :code, :group_id, :tenant_id, 'system')"
                    ), {"name": name, "code": code, "group_id": group_ids[group_code], "tenant_id": tenant_id})
            
            # Insert default voucher types
            voucher_types_data = [
                ('Sales', 'SAL', 'SAL-'),
                ('Purchase', 'PUR', 'PUR-'),
                ('Payment', 'PAY', 'PAY-'),
                ('Receipt', 'REC', 'REC-'),
                ('Journal', 'JV', 'JV-'),
            ]
            
            for name, code, prefix in voucher_types_data:
                existing = session.execute(text(
                    "SELECT id FROM voucher_types WHERE code = :code AND tenant_id = :tenant_id"
                ), {"code": code, "tenant_id": tenant_id}).fetchone()
                
                if not existing:
                    session.execute(text(
                        "INSERT INTO voucher_types (name, code, prefix, tenant_id) VALUES (:name, :code, :prefix, :tenant_id)"
                    ), {"name": name, "code": code, "prefix": prefix, "tenant_id": tenant_id})
            
            session.commit()
            print("[OK] Account master data inserted")
            
    except Exception as e:
        print(f"[ERROR] Error inserting account master data: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running default data migration...")
    insert_default_data()
    print("Default data migration completed!")