#!/usr/bin/env python3
"""
Migration 040: Add is_inventory_item column to products table
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add is_inventory_item column to products table"""
    print("Running migration 040...")
    
    with db_manager.get_session() as session:
        session.execute(text("""
            ALTER TABLE products 
            ADD COLUMN IF NOT EXISTS is_inventory_item BOOLEAN DEFAULT TRUE
        """))
        
        session.commit()
        print("[OK] Migration 040 completed")

def downgrade():
    """Remove is_inventory_item column"""
    print("Rolling back migration 040...")
    
    with db_manager.get_session() as session:
        session.execute(text("ALTER TABLE products DROP COLUMN IF EXISTS is_inventory_item"))
        session.commit()
        print("[OK] Migration 040 rolled back")

if __name__ == "__main__":
    upgrade()
