#!/usr/bin/env python3
"""
Add is_deleted columns to sales_orders and purchase_orders tables
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def add_is_deleted_columns():
    """Add is_deleted columns to tables"""
    print("Adding is_deleted columns...")
    
    try:
        with db_manager.get_session() as session:
            # Add is_deleted to sales_orders
            session.execute(text("""
                ALTER TABLE sales_orders 
                ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
            """))
            
            # Add is_deleted to purchase_orders
            session.execute(text("""
                ALTER TABLE purchase_orders 
                ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
            """))
            
            session.commit()
            print("[OK] is_deleted columns added successfully")
            
    except Exception as e:
        print(f"[ERROR] Error adding columns: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running migration: Add is_deleted columns...")
    add_is_deleted_columns()
    print("Migration completed!")
