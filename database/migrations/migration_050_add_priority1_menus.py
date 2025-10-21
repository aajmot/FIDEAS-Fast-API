from sqlalchemy import text
from core.database.connection import db_manager

def run_migration():
    with db_manager.get_session() as session:
        # Add GST Reports menu
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, sort_order, is_active, parent_menu_id)
            VALUES ('GST Reports', 'GST_REPORTS', 'ACCOUNT', '/account/gst-reports', '📊', 25, true, NULL)
            ON CONFLICT (menu_code) DO NOTHING;
        """))
        
        # Add Stock Valuation menu
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, sort_order, is_active, parent_menu_id)
            VALUES ('Stock Valuation', 'STOCK_VALUATION', 'INVENTORY', '/inventory/stock-valuation', '💰', 50, true, NULL)
            ON CONFLICT (menu_code) DO NOTHING;
        """))
        
        # Add Stock Aging menu
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, route, icon, sort_order, is_active, parent_menu_id)
            VALUES ('Stock Aging', 'STOCK_AGING', 'INVENTORY', '/inventory/stock-aging', '⏰', 51, true, NULL)
            ON CONFLICT (menu_code) DO NOTHING;
        """))
        
        session.commit()
        print("✅ Priority 1 menus added successfully")

if __name__ == "__main__":
    run_migration()
