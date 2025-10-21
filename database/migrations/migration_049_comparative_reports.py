"""
Migration 049: Add Comparative Reports Menu Items
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade(session):
    """Add comparative reports menu items"""
    
    module_code = 'ACCOUNT'
    
    # Get Reports parent menu ID
    result = session.execute(text("""
        SELECT id FROM menu_master 
        WHERE menu_code = 'ACCOUNT_REPORTS' AND module_code = :module_code
    """), {"module_code": module_code})
    reports_menu = result.fetchone()
    
    if not reports_menu:
        print("Reports menu not found")
        return
    
    reports_parent_id = reports_menu[0]
    
    # Add Comparative Reports menu
    session.execute(text("""
        INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, parent_menu_id, sort_order, is_active)
        VALUES ('Comparative Reports', 'COMPARATIVE_REPORTS', :module_code, '/account/reports/comparative', '📊', :parent_id, 53, true)
        ON CONFLICT (menu_code) DO NOTHING
    """), {"parent_id": reports_parent_id, "module_code": module_code})
    
    # Add Budget vs Actual menu
    session.execute(text("""
        INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, parent_menu_id, sort_order, is_active)
        VALUES ('Budget vs Actual', 'BUDGET_VS_ACTUAL', :module_code, '/account/reports/budget-vs-actual', '💰', :parent_id, 54, true)
        ON CONFLICT (menu_code) DO NOTHING
    """), {"parent_id": reports_parent_id, "module_code": module_code})
    
    session.commit()
    print("[OK] Migration 049: Comparative reports menu items added successfully")

if __name__ == "__main__":
    with db_manager.get_session() as session:
        upgrade(session)
