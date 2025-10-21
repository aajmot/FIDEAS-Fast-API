"""
Migration: Add is_deleted column to vouchers table
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add is_deleted column to vouchers table"""
    with db_manager.get_session() as session:
        try:
            # Add is_deleted column with default False
            session.execute(text("""
                ALTER TABLE vouchers 
                ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
            """))
            
            session.commit()
            print("✓ Added is_deleted column to vouchers table")
            
        except Exception as e:
            session.rollback()
            print(f"✗ Error adding is_deleted column: {str(e)}")
            raise

def downgrade():
    """Remove is_deleted column from vouchers table"""
    with db_manager.get_session() as session:
        try:
            session.execute(text("""
                ALTER TABLE vouchers 
                DROP COLUMN IF EXISTS is_deleted;
            """))
            
            session.commit()
            print("✓ Removed is_deleted column from vouchers table")
            
        except Exception as e:
            session.rollback()
            print(f"✗ Error removing is_deleted column: {str(e)}")
            raise

if __name__ == "__main__":
    print("Running migration: Add is_deleted to vouchers")
    upgrade()
    print("Migration completed successfully")
