"""
Fix menu routes to match React App.tsx routes
"""

import psycopg2
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
    cur = conn.cursor()
    
    try:
        print("Fixing menu routes...")
        
        # Route mappings: menu_code -> correct_route
        route_fixes = {
            # Admin routes
            'USER_MGMT': '/admin/user-management',
            'ROLE_MGMT': '/admin/role-management',
            'USER_ROLE_MAPPING': '/admin/user-role-mapping',
            'LEGAL_ENTITY_MGMT': '/admin/legal-entity',
            'FINANCIAL_YEAR': '/admin/financial-years',
            'AGENCY_MGMT': '/admin/agency-management',
            
            # Inventory routes
            'UNIT_MASTER': '/inventory/unit-management',
            'CATEGORY_MGMT': '/inventory/category-management',
            'PRODUCT_MGMT': '/inventory/product-management',
            'PRODUCT_BATCH_MGMT': '/inventory/batch-management',
            'INV_CUSTOMER_MGMT': '/inventory/customer-management',
            'SUPPLIER_MGMT': '/inventory/supplier-management',
            'PURCHASE_ORDER': '/inventory/purchase-order',
            'SALES_ORDER': '/inventory/sales-order',
            
            # Account routes
            'CHART_ACCOUNTS': '/account/chart-accounts',
            'LEDGER': '/account/ledger',
            'JOURNAL': '/account/journal',
            'VOUCHERS': '/account/vouchers',
            'PAYMENTS': '/account/payments',
            'REPORTS': '/account/reports',
            
            # Clinic routes
            'PATIENT_MGMT': '/clinic/patient-management',
            'DOCTOR_MGMT': '/clinic/doctor-management',
            'APPOINTMENT_MGMT': '/clinic/appointments',
            'MEDICAL_RECORDS': '/clinic/medical-records',
            'PRESCRIPTION_MGMT': '/clinic/prescriptions',
            'CLINIC_BILLING': '/clinic/billings',
            'EMPLOYEE_MGMT': '/clinic/employees',
            
            # Diagnostic routes
            'TEST_CATEGORY_MGMT': '/diagnostic/test-category',
            'TEST_MASTER': '/diagnostic/test-master',
            'TEST_ORDER_MGMT': '/diagnostic/test-order',
            'TEST_RESULT_MGMT': '/diagnostic/test-result',
        }
        
        for menu_code, route in route_fixes.items():
            cur.execute("""
                UPDATE menu_master 
                SET route = %s 
                WHERE menu_code = %s
            """, (route, menu_code))
            print(f"Updated {menu_code} -> {route}")
        
        conn.commit()
        print(f"\nFixed {len(route_fixes)} menu routes")
        
    except Exception as e:
        conn.rollback()
        print(f"Fix failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run_fix()
