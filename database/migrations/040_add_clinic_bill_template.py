#!/usr/bin/env python3
"""
Migration 040: Add CLINIC_BILL transaction template
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add CLINIC_BILL template"""
    print("Running migration 040...")
    
    with db_manager.get_session() as session:
        session.execute(text("""
            INSERT INTO transaction_templates (name, code, transaction_type, description, tenant_id, created_by)
            SELECT 
                'Clinic Billing Posting',
                'CLINIC_POST',
                'CLINIC_BILL',
                'Default posting template for clinic billing',
                t.id,
                'system'
            FROM tenants t
            WHERE NOT EXISTS (
                SELECT 1 FROM transaction_templates tt 
                WHERE tt.transaction_type = 'CLINIC_BILL' AND tt.tenant_id = t.id
            )
        """))
        
        session.execute(text("""
            INSERT INTO transaction_template_rules 
            (template_id, line_number, account_type, entry_type, amount_source, narration, tenant_id)
            SELECT 
                tt.id, 1, 'ACCOUNTS_RECEIVABLE', 'DEBIT', 'TOTAL_AMOUNT', 'Clinic billing', tt.tenant_id
            FROM transaction_templates tt
            WHERE tt.transaction_type = 'CLINIC_BILL'
            AND NOT EXISTS (
                SELECT 1 FROM transaction_template_rules ttr 
                WHERE ttr.template_id = tt.id AND ttr.line_number = 1
            )
        """))
        
        session.execute(text("""
            INSERT INTO transaction_template_rules 
            (template_id, line_number, account_type, entry_type, amount_source, narration, tenant_id)
            SELECT 
                tt.id, 2, 'CLINIC_REVENUE', 'CREDIT', 'TOTAL_AMOUNT', 'Clinic revenue', tt.tenant_id
            FROM transaction_templates tt
            WHERE tt.transaction_type = 'CLINIC_BILL'
            AND NOT EXISTS (
                SELECT 1 FROM transaction_template_rules ttr 
                WHERE ttr.template_id = tt.id AND ttr.line_number = 2
            )
        """))
        
        session.commit()
        print("[OK] Migration 040 completed")

def downgrade():
    """Remove CLINIC_BILL template"""
    print("Rolling back migration 040...")
    
    with db_manager.get_session() as session:
        session.execute(text("DELETE FROM transaction_templates WHERE transaction_type = 'CLINIC_BILL'"))
        session.commit()
        print("[OK] Migration 040 rolled back")

if __name__ == "__main__":
    upgrade()
