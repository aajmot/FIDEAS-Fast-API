#!/usr/bin/env python3
"""
Add tax_id field to customers table
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add tax_id column to customers table"""
    print("Adding tax_id column to customers table...")
    
    try:
        with db_manager.get_session() as session:
            # Add tax_id column to customers table
            session.execute(text("""
                ALTER TABLE customers 
                ADD COLUMN IF NOT EXISTS tax_id VARCHAR(50);
            """))
            
            session.commit()
            print("[OK] tax_id column added to customers table successfully")
            
    except Exception as e:
        print(f"[ERROR] Error adding tax_id column: {str(e)}")
        raise

def downgrade():
    """Remove tax_id column from customers table"""
    print("Removing tax_id column from customers table...")
    
    try:
        with db_manager.get_session() as session:
            # Remove tax_id column from customers table
            session.execute(text("""
                ALTER TABLE customers 
                DROP COLUMN IF EXISTS tax_id;
            """))
            
            session.commit()
            print("[OK] tax_id column removed from customers table successfully")
            
    except Exception as e:
        print(f"[ERROR] Error removing tax_id column: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running customer tax_id migration...")
    upgrade()
    print("Migration completed!")