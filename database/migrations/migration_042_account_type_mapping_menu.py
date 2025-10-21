#!/usr/bin/env python3
"""
Migration 042: Add Account Type Mappings menu entry
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add Account Type Mappings menu"""
    print("Running migration 042...")
    
    with db_manager.get_session() as session:
        # Get Admin Transaction parent menu
        result = session.execute(text("""
            SELECT id FROM menu_master 
            WHERE menu_code = 'ADMIN_TRANSACTION' AND module_code = 'ADMIN'
        """)).fetchone()
        
        if result:
            parent_id = result[0]
            
            # Insert Account Type Mappings menu if not exists
            existing = session.execute(text("""
                SELECT id FROM menu_master WHERE menu_code = 'ACCOUNT_TYPE_MAPPINGS'
            """)).fetchone()
            
            if not existing:
                session.execute(text("""
                    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order, is_active)
                    VALUES ('Account Type Mappings', 'ACCOUNT_TYPE_MAPPINGS', 'ADMIN', :parent_id, '🔗', '/admin/account-type-mappings', 4, true)
                """), {"parent_id": parent_id})
            
            session.commit()
            print("[OK] Migration 042 completed - Menu entry ready")
        else:
            print("[SKIP] Admin Transaction menu not found")

def downgrade():
    """Remove Account Type Mappings menu"""
    print("Rolling back migration 042...")
    
    with db_manager.get_session() as session:
        session.execute(text("""
            DELETE FROM menu_master WHERE menu_code = 'ACCOUNT_TYPE_MAPPINGS'
        """))
        session.commit()
        print("[OK] Migration 042 rolled back")

if __name__ == "__main__":
    upgrade()
