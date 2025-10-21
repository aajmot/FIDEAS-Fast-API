#!/usr/bin/env python3
"""
Migration 039: Add Transaction Templates menu to Admin module
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add Transaction Templates menu"""
    print("Running migration 039...")
    
    with db_manager.get_session() as session:
        # Insert menu under Admin > Transaction
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order, is_active)
            SELECT 
                'Transaction Templates',
                'TRANSACTION_TEMPLATES',
                'ADMIN',
                (SELECT id FROM menu_master WHERE menu_code = 'ADMIN_TRANSACTION' LIMIT 1),
                '📋',
                '/admin/transaction-templates',
                4,
                TRUE
            WHERE NOT EXISTS (
                SELECT 1 FROM menu_master WHERE menu_code = 'TRANSACTION_TEMPLATES'
            )
        """))
        
        session.commit()
        print("[OK] Migration 039 completed")

def downgrade():
    """Remove Transaction Templates menu"""
    print("Rolling back migration 039...")
    
    with db_manager.get_session() as session:
        session.execute(text("DELETE FROM menu_master WHERE menu_code = 'TRANSACTION_TEMPLATES'"))
        session.commit()
        print("[OK] Migration 039 rolled back")

if __name__ == "__main__":
    upgrade()
