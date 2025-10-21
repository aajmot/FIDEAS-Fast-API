#!/usr/bin/env python3
"""
Migration 041: Create account type mapping table
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Create account type mapping table"""
    print("Running migration 041...")
    
    with db_manager.get_session() as session:
        # Create account_type_mappings table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS account_type_mappings (
                id SERIAL PRIMARY KEY,
                account_type VARCHAR(50) NOT NULL,
                account_id INTEGER NOT NULL REFERENCES account_masters(id) ON DELETE CASCADE,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                UNIQUE(account_type, tenant_id)
            )
        """))
        
        # Insert default mappings for existing tenants
        session.execute(text("""
            INSERT INTO account_type_mappings (account_type, account_id, tenant_id, created_by)
            SELECT 'ACCOUNTS_RECEIVABLE', am.id, am.tenant_id, 'system'
            FROM account_masters am
            WHERE am.code = 'AR001'
            AND NOT EXISTS (
                SELECT 1 FROM account_type_mappings atm 
                WHERE atm.account_type = 'ACCOUNTS_RECEIVABLE' AND atm.tenant_id = am.tenant_id
            )
        """))
        
        session.execute(text("""
            INSERT INTO account_type_mappings (account_type, account_id, tenant_id, created_by)
            SELECT 'ACCOUNTS_PAYABLE', am.id, am.tenant_id, 'system'
            FROM account_masters am
            WHERE am.code = 'AP001'
            AND NOT EXISTS (
                SELECT 1 FROM account_type_mappings atm 
                WHERE atm.account_type = 'ACCOUNTS_PAYABLE' AND atm.tenant_id = am.tenant_id
            )
        """))
        
        session.execute(text("""
            INSERT INTO account_type_mappings (account_type, account_id, tenant_id, created_by)
            SELECT 'SALES_REVENUE', am.id, am.tenant_id, 'system'
            FROM account_masters am
            WHERE am.code = 'SR001'
            AND NOT EXISTS (
                SELECT 1 FROM account_type_mappings atm 
                WHERE atm.account_type = 'SALES_REVENUE' AND atm.tenant_id = am.tenant_id
            )
        """))
        
        session.execute(text("""
            INSERT INTO account_type_mappings (account_type, account_id, tenant_id, created_by)
            SELECT 'INVENTORY', am.id, am.tenant_id, 'system'
            FROM account_masters am
            WHERE am.code = 'INV001'
            AND NOT EXISTS (
                SELECT 1 FROM account_type_mappings atm 
                WHERE atm.account_type = 'INVENTORY' AND atm.tenant_id = am.tenant_id
            )
        """))
        
        session.execute(text("""
            INSERT INTO account_type_mappings (account_type, account_id, tenant_id, created_by)
            SELECT 'COGS', am.id, am.tenant_id, 'system'
            FROM account_masters am
            WHERE am.code = 'PE001'
            AND NOT EXISTS (
                SELECT 1 FROM account_type_mappings atm 
                WHERE atm.account_type = 'COGS' AND atm.tenant_id = am.tenant_id
            )
        """))
        
        session.execute(text("""
            INSERT INTO account_type_mappings (account_type, account_id, tenant_id, created_by)
            SELECT 'TAX_PAYABLE', am.id, am.tenant_id, 'system'
            FROM account_masters am
            WHERE am.code = 'STP001'
            AND NOT EXISTS (
                SELECT 1 FROM account_type_mappings atm 
                WHERE atm.account_type = 'TAX_PAYABLE' AND atm.tenant_id = am.tenant_id
            )
        """))
        
        session.commit()
        print("[OK] Migration 041 completed")

def downgrade():
    """Remove account type mapping table"""
    print("Rolling back migration 041...")
    
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS account_type_mappings"))
        session.commit()
        print("[OK] Migration 041 rolled back")

if __name__ == "__main__":
    upgrade()
