#!/usr/bin/env python3
"""
Migration 043: Contra Voucher Support
Adds contra voucher type and menu entry
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def run_migration():
    """Add contra voucher support"""
    print("Running Migration 043: Contra Voucher Support...")
    
    with db_manager.get_session() as session:
        try:
            # Add Contra voucher type for all tenants
            session.execute(text("""
                INSERT INTO voucher_types (name, code, prefix, tenant_id, is_active)
                SELECT 'Contra', 'CONTRA', 'CNT-', id, true
                FROM tenants
                WHERE NOT EXISTS (
                    SELECT 1 FROM voucher_types 
                    WHERE code = 'CONTRA' AND tenant_id = tenants.id
                )
            """))
            
            # Add Contra menu entry
            session.execute(text("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order)
                SELECT 'Contra', 'CONTRA', 'ACCOUNT', 
                    (SELECT id FROM menu_master WHERE menu_code = 'ACCOUNT_TRANSACTION' LIMIT 1),
                    '🔄', '/account/contra', 6
                WHERE NOT EXISTS (SELECT 1 FROM menu_master WHERE menu_code = 'CONTRA')
            """))
            
            session.commit()
            print("[OK] Migration 043 completed successfully")
            
        except Exception as e:
            session.rollback()
            print(f"[ERROR] Migration 043 failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
