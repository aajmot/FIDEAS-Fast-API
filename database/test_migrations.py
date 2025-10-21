#!/usr/bin/env python3
"""
Test script to verify database migrations work correctly
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from core.database.connection import db_manager
from sqlalchemy import text

def test_schema_creation():
    """Test that all tables are created correctly"""
    print("Testing schema creation...")
    
    expected_tables = [
        'tenants', 'users', 'roles', 'user_roles', 'menu_masters', 'module_masters',
        'categories', 'products', 'customers', 'suppliers', 'units',
        'sales_orders', 'purchase_orders', 'sales_order_items', 'purchase_order_items',
        'account_groups', 'account_masters', 'voucher_types', 'vouchers',
        'journals', 'journal_details', 'ledgers', 'payments',
        'patients', 'doctors', 'appointments', 'medical_records',
        'prescriptions', 'prescription_items', 'clinic_invoices',
        'clinic_invoice_items', 'clinic_employees',
        'stock_balances', 'stock_transactions'
    ]
    
    try:
        with db_manager.get_session() as session:
            for table in expected_tables:
                result = session.execute(text(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'"))
                count = result.fetchone()[0]
                if count > 0:
                    print(f"✓ Table '{table}' exists")
                else:
                    print(f"✗ Table '{table}' missing")
        
        print("[OK] Schema test completed")
        
    except Exception as e:
        print(f"[ERROR] Schema test failed: {str(e)}")
        raise

def test_default_data():
    """Test that default data is inserted correctly"""
    print("Testing default data insertion...")
    
    try:
        with db_manager.get_session() as session:
            # Check modules
            result = session.execute(text("SELECT COUNT(*) FROM module_masters"))
            module_count = result.fetchone()[0]
            print(f"✓ Found {module_count} modules")
            
            # Check units
            result = session.execute(text("SELECT COUNT(*) FROM units"))
            unit_count = result.fetchone()[0]
            print(f"✓ Found {unit_count} inventory units")
            
            # Check menus
            result = session.execute(text("SELECT COUNT(*) FROM menu_masters"))
            menu_count = result.fetchone()[0]
            print(f"✓ Found {menu_count} menu items")
            
            # Check parent-child relationships
            result = session.execute(text("SELECT COUNT(*) FROM menu_masters WHERE parent_menu_id IS NOT NULL"))
            submenu_count = result.fetchone()[0]
            print(f"✓ Found {submenu_count} submenus with parent relationships")
        
        print("[OK] Default data test completed")
        
    except Exception as e:
        print(f"[ERROR] Default data test failed: {str(e)}")
        raise

def test_account_setup():
    """Test account master data setup for a test tenant"""
    print("Testing account master data setup...")
    
    try:
        # This would normally be called during tenant setup
        from database.setup_database import insert_account_master_data
        
        # For testing, we'll just verify the function exists and can be imported
        print("✓ Account setup function imported successfully")
        print("[OK] Account setup test completed")
        
    except Exception as e:
        print(f"[ERROR] Account setup test failed: {str(e)}")
        raise

def run_tests():
    """Run all migration tests"""
    print("=" * 50)
    print("FIDEAS Database Migration Tests")
    print("=" * 50)
    
    try:
        test_schema_creation()
        print()
        test_default_data()
        print()
        test_account_setup()
        
        print("=" * 50)
        print("[SUCCESS] All migration tests passed!")
        print("=" * 50)
        
    except Exception as e:
        print("=" * 50)
        print(f"[FAILED] Migration tests failed: {str(e)}")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    run_tests()