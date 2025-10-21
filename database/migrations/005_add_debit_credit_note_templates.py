#!/usr/bin/env python3
"""
Add Debit Note and Credit Note transaction templates
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def add_note_templates():
    """Add debit and credit note templates"""
    print("Adding debit and credit note templates...")
    
    try:
        with db_manager.get_session() as session:
            # Check if templates already exist
            existing = session.execute(text("""
                SELECT code FROM transaction_templates 
                WHERE code IN ('DEBIT_NOTE', 'CREDIT_NOTE')
            """)).fetchall()
            
            existing_codes = [row[0] for row in existing]
            
            # Add Debit Note template
            if 'DEBIT_NOTE' not in existing_codes:
                session.execute(text("""
                    INSERT INTO transaction_templates 
                    (name, code, transaction_type, description, is_active, tenant_id, created_by)
                    VALUES 
                    ('Debit Note Posting', 'DEBIT_NOTE', 'DEBIT_NOTE', 
                     'Accounting entries for debit notes issued to suppliers', 
                     TRUE, 1, 'system')
                """))
                print("Added Debit Note template")
            
            # Add Credit Note template
            if 'CREDIT_NOTE' not in existing_codes:
                session.execute(text("""
                    INSERT INTO transaction_templates 
                    (name, code, transaction_type, description, is_active, tenant_id, created_by)
                    VALUES 
                    ('Credit Note Posting', 'CREDIT_NOTE', 'CREDIT_NOTE', 
                     'Accounting entries for credit notes issued to customers', 
                     TRUE, 1, 'system')
                """))
                print("Added Credit Note template")
            
            session.commit()
            print("[OK] Templates added successfully")
            
    except Exception as e:
        print(f"[ERROR] Error adding templates: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running migration: Add debit/credit note templates...")
    add_note_templates()
    print("Migration completed!")
