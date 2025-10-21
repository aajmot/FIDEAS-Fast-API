#!/usr/bin/env python3
"""
Migration 046: Add Cash Book menu entry
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def run_migration():
    """Add Cash Book menu entry"""
    print("Running Migration 046: Add Cash Book menu entry...")
    
    with db_manager.get_session() as session:
        try:
            # Add Cash Book menu entry
            session.execute(text("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order)
                SELECT 'Cash Book', 'CASH_BOOK', 'ACCOUNT', 
                    (SELECT id FROM menu_master WHERE menu_code = 'ACCOUNT_REPORTS' LIMIT 1),
                    '💰', '/account/cash-book', 3
                WHERE NOT EXISTS (SELECT 1 FROM menu_master WHERE menu_code = 'CASH_BOOK')
            """))
            
            session.commit()
            print("[OK] Migration 046 completed successfully")
            
        except Exception as e:
            session.rollback()
            print(f"[ERROR] Migration 046 failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
