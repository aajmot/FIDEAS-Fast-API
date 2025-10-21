#!/usr/bin/env python3
"""
Migration 041: Add CLINIC and DIAGNOSTIC voucher types
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add CLINIC and DIAGNOSTIC voucher types"""
    print("Running migration 041...")
    
    with db_manager.get_session() as session:
        session.execute(text("""
            INSERT INTO voucher_types (name, code, prefix, tenant_id)
            SELECT 
                'Clinic Bill', 'CLINIC', 'CB', t.id
            FROM tenants t
            WHERE NOT EXISTS (
                SELECT 1 FROM voucher_types vt 
                WHERE vt.code = 'CLINIC' AND vt.tenant_id = t.id
            )
        """))
        
        session.execute(text("""
            INSERT INTO voucher_types (name, code, prefix, tenant_id)
            SELECT 
                'Diagnostic', 'DIAG', 'DG', t.id
            FROM tenants t
            WHERE NOT EXISTS (
                SELECT 1 FROM voucher_types vt 
                WHERE vt.code = 'DIAG' AND vt.tenant_id = t.id
            )
        """))
        
        session.commit()
        print("[OK] Migration 041 completed")

def downgrade():
    """Remove CLINIC and DIAGNOSTIC voucher types"""
    print("Rolling back migration 041...")
    
    with db_manager.get_session() as session:
        session.execute(text("DELETE FROM voucher_types WHERE code IN ('CLINIC', 'DIAG')"))
        session.commit()
        print("[OK] Migration 041 rolled back")

if __name__ == "__main__":
    upgrade()
