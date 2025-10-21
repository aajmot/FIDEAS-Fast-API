#!/usr/bin/env python3
"""
Add Order Commission Menu Items Migration
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def add_order_commission_menus():
    """Add order commission menu items"""
    print("Adding order commission menu items...")
    
    try:
        with db_manager.get_session() as session:
            # Get the next sort order for inventory and diagnostic modules
            result = session.execute(text("SELECT MAX(sort_order) FROM menu_master WHERE module_code IN ('INVENTORY', 'DIAGNOSTIC')"))
            max_sort = result.scalar() or 0
            
            # Insert menu items
            menu_sql_1 = """
            INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order, is_active)
            SELECT 'Order Commission', 'ORDER_COMMISSION_INV', 'INVENTORY', 
                   (SELECT id FROM menu_master WHERE menu_code = 'SALES_ORDER' AND module_code = 'INVENTORY'),
                   'FileText', '/inventory/order-commission', :sort1, TRUE
            WHERE NOT EXISTS (
                SELECT 1 FROM menu_master WHERE menu_code = 'ORDER_COMMISSION_INV'
            )
            """
            
            menu_sql_2 = """
            INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order, is_active)
            SELECT 'Order Commission', 'ORDER_COMMISSION_DIAG', 'DIAGNOSTIC', 
                   (SELECT id FROM menu_master WHERE menu_code = 'TEST_ORDER' AND module_code = 'DIAGNOSTIC'),
                   'FileText', '/diagnostic/order-commission', :sort2, TRUE
            WHERE NOT EXISTS (
                SELECT 1 FROM menu_master WHERE menu_code = 'ORDER_COMMISSION_DIAG'
            )
            """
            
            session.execute(text(menu_sql_1), {'sort1': max_sort + 1})
            session.execute(text(menu_sql_2), {'sort2': max_sort + 2})
            session.commit()
            print("[OK] Order commission menu items added successfully")
            
    except Exception as e:
        print(f"[ERROR] Error adding order commission menus: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running order commission menus migration...")
    add_order_commission_menus()
    print("Order commission menus migration completed!")
