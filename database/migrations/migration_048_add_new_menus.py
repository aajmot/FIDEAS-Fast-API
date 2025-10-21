"""
Migration 048: Add New Menu Items for Production Features
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade(session):
    """Add new menu items"""
    
    module_code = 'ACCOUNT'
    
    # Get Reports parent menu ID
    result = session.execute(text("""
        SELECT id FROM menu_master 
        WHERE menu_name = 'Reports' AND module_code = :module_code
    """), {"module_code": module_code})
    reports_menu = result.fetchone()
    
    if not reports_menu:
        # Create Reports parent menu if doesn't exist
        result = session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, sort_order, is_active)
            VALUES ('Reports', 'ACCOUNT_REPORTS', :module_code, '/account/reports', '📈', 50, true)
            RETURNING id
        """), {"module_code": module_code})
        reports_menu = result.fetchone()
    
    reports_parent_id = reports_menu[0]
    
    # Add AR Aging Report menu
    session.execute(text("""
        INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, parent_menu_id, sort_order, is_active)
        VALUES ('AR Aging Report', 'AR_AGING', :module_code, '/account/reports/ar-aging', '📊', :parent_id, 51, true)
        ON CONFLICT (menu_code) DO NOTHING
    """), {"parent_id": reports_parent_id, "module_code": module_code})
    
    # Add AP Aging Report menu
    session.execute(text("""
        INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, parent_menu_id, sort_order, is_active)
        VALUES ('AP Aging Report', 'AP_AGING', :module_code, '/account/reports/ap-aging', '📊', :parent_id, 52, true)
        ON CONFLICT (menu_code) DO NOTHING
    """), {"parent_id": reports_parent_id, "module_code": module_code})
    
    # Add Audit Trail menu
    session.execute(text("""
        INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, parent_menu_id, sort_order, is_active)
        VALUES ('Audit Trail', 'AUDIT_TRAIL', :module_code, '/account/audit-trail', '📜', NULL, 60, true)
        ON CONFLICT (menu_code) DO NOTHING
    """), {"module_code": module_code})
    
    # Add GST Calculator menu (under Utilities)
    result = session.execute(text("""
        SELECT id FROM menu_master 
        WHERE menu_name = 'Utilities' AND module_code = :module_code
    """), {"module_code": module_code})
    utilities_menu = result.fetchone()
    
    if not utilities_menu:
        # Create Utilities parent menu
        result = session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, sort_order, is_active)
            VALUES ('Utilities', 'ACCOUNT_UTILITIES', :module_code, '/account/utilities', '🔧', 70, true)
            RETURNING id
        """), {"module_code": module_code})
        utilities_menu = result.fetchone()
    
    utilities_parent_id = utilities_menu[0]
    
    # Add GST Calculator menu
    session.execute(text("""
        INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, parent_menu_id, sort_order, is_active)
        VALUES ('GST Calculator', 'GST_CALCULATOR', :module_code, '/account/utilities/gst-calculator', '🧮', :parent_id, 71, true)
        ON CONFLICT (menu_code) DO NOTHING
    """), {"parent_id": utilities_parent_id, "module_code": module_code})
    
    session.commit()
    print("[OK] Migration 048: New menu items added successfully")

if __name__ == "__main__":
    with db_manager.get_session() as session:
        upgrade(session)
