#!/usr/bin/env python3
"""
Fix menu routes to match App.tsx routes
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def fix_menu_routes():
    """Update menu routes to match App.tsx"""
    print("Fixing menu routes...")
    
    # Map of menu codes to correct routes based on App.tsx
    route_mappings = {
        # Admin routes
        'USER_MGMT': '/admin/user-management',
        'ROLE_MGMT': '/admin/role-management',
        'USER_ROLE_MAPPING': '/admin/user-role-mapping',
        'MENU_ACCESS': '/admin/menu-access',
        'TENANT_UPDATE': '/admin/tenant-update',
        'TRANSACTION_TEMPLATES': '/admin/transaction-templates',
        'ACCOUNT_TYPE_MAPPINGS': '/admin/account-type-mappings',
        'LEGAL_ENTITY': '/admin/legal-entity',
        'LEGAL_ENTITY_MGMT': '/admin/legal-entity',
        'FINANCIAL_YEAR': '/admin/financial-year',
        'AGENCY_MGMT': '/admin/agency-management',
        'AGENCY_COMMISSION_SETUP': '/admin/agency-commission-setup',
        
        # Inventory routes
        'UNIT_MASTER': '/inventory/units',
        'UNIT_MGMT': '/inventory/units',
        'CATEGORY_MGMT': '/inventory/category-management',
        'PRODUCT_MGMT': '/inventory/product-management',
        'CUSTOMER_MGMT': '/inventory/customer-management',
        'INV_CUSTOMER_MGMT': '/inventory/customer-management',
        'SUPPLIER_MGMT': '/inventory/supplier-management',
        'PURCHASE_ORDER': '/inventory/purchase-order',
        'SALES_ORDER': '/inventory/sales-order',
        'ORDER_COMMISSION_INV': '/inventory/order-commission',
        'PRODUCT_WASTE': '/inventory/product-waste',
        'STOCK_DETAILS': '/inventory/stock-details',
        'STOCK_METER': '/inventory/stock-meter',
        'STOCK_TRACKING': '/inventory/stock-tracking',
        
        # Account routes
        'CHART_ACCOUNTS': '/account/chart-accounts',
        'ACCOUNT_GROUPS': '/account/account-groups',
        'VOUCHER_SERIES': '/account/voucher-series',
        'COST_CENTERS': '/account/cost-centers',
        'BUDGETS': '/account/budgets',
        'TAX_MANAGEMENT': '/account/tax-management',
        'CURRENCY_MANAGEMENT': '/account/currency-management',
        'BANK_RECONCILIATION': '/account/bank-reconciliation',
        'JOURNAL': '/account/journal',
        'JOURNAL_ENTRY': '/account/journal',
        'VOUCHERS': '/account/vouchers',
        'PAYMENTS': '/account/payments',
        'RECEIPTS': '/account/receipts',
        'RECURRING_VOUCHERS': '/account/recurring-vouchers',
        'CONTRA': '/account/contra',
        'CREDIT_NOTE': '/account/credit-notes',
        'DEBIT_NOTE': '/account/debit-notes',
        'AGING_ANALYSIS': '/account/aging-analysis',
        'TDS_MANAGEMENT': '/account/tds-management',
        'LEDGER': '/account/ledger',
        'DAY_BOOK': '/account/day-book',
        'CASH_BOOK': '/account/cash-book',
        'BANK_BOOK': '/account/bank-book',
        'TRIAL_BALANCE': '/account/reports',
        'PROFIT_LOSS': '/account/reports',
        'BALANCE_SHEET': '/account/reports',
        'CASH_FLOW': '/account/reports',
        'REPORTS': '/account/reports',
        'OUTSTANDING_REPORTS': '/account/outstanding-reports',
        'COMPARATIVE_REPORTS': '/account/comparative-reports',
        
        # Clinic routes
        'PATIENT_MGMT': '/clinic/patient-management',
        'DOCTOR_MGMT': '/clinic/doctor-management',
        'APPOINTMENT_MGMT': '/clinic/appointments',
        'APPOINTMENTS': '/clinic/appointments',
        'MEDICAL_RECORDS': '/clinic/medical-records',
        'PRESCRIPTION_MGMT': '/clinic/prescriptions',
        'PRESCRIPTIONS': '/clinic/prescriptions',
        'CLINIC_BILLING': '/clinic/billings',
        'BILLINGS': '/clinic/billings',
        'BILLING_MASTER': '/clinic/billing-master',
        'TEST_CATEGORY': '/clinic/test-category',
        'TEST_MASTER': '/clinic/test-master',
        
        # Diagnostic routes
        'DIAGNOSTIC_PATIENT_MGMT': '/diagnostic/patient-management',
        'DIAGNOSTIC_DOCTOR_MGMT': '/diagnostic/doctor-management',
        'DIAGNOSTIC_TEST_CATEGORY': '/diagnostic/test-category',
        'DIAGNOSTIC_TEST_MASTER': '/diagnostic/test-master',
        'TEST_PANEL': '/diagnostic/test-panel',
        'TEST_ORDER': '/diagnostic/test-order',
        'TEST_RESULT': '/diagnostic/test-result',
        'ORDER_COMMISSION_DIAG': '/diagnostic/order-commission',
    }
    
    try:
        with db_manager.get_session() as session:
            updated_count = 0
            for menu_code, route in route_mappings.items():
                result = session.execute(text("""
                    UPDATE menu_master 
                    SET route = :route 
                    WHERE menu_code = :menu_code
                """), {"route": route, "menu_code": menu_code})
                
                if result.rowcount > 0:
                    updated_count += result.rowcount
                    print(f"Updated {menu_code} -> {route}")
            
            session.commit()
            print(f"[OK] Updated {updated_count} menu routes successfully")
            
    except Exception as e:
        print(f"[ERROR] Error updating routes: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running migration: Fix menu routes...")
    fix_menu_routes()
    print("Migration completed!")
