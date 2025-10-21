"""
Migration: Add updated_at and updated_by columns to tenant_module_mapping table
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    """Add updated_at and updated_by columns"""
    with db_manager.get_session() as session:
        # Add updated_at column
        session.execute(text("""
            ALTER TABLE tenant_module_mapping 
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """))
        
        # Add updated_by column
        session.execute(text("""
            ALTER TABLE tenant_module_mapping 
            ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100)
        """))
        
        # Set is_active default to true if not already set
        session.execute(text("""
            ALTER TABLE tenant_module_mapping 
            ALTER COLUMN is_active SET DEFAULT true
        """))
        
        session.commit()
        print("Added updated_at and updated_by columns to tenant_module_mapping")

def downgrade():
    """Remove updated_at and updated_by columns"""
    with db_manager.get_session() as session:
        session.execute(text("ALTER TABLE tenant_module_mapping DROP COLUMN IF EXISTS updated_at"))
        session.execute(text("ALTER TABLE tenant_module_mapping DROP COLUMN IF EXISTS updated_by"))
        session.commit()
        print("Removed updated_at and updated_by columns from tenant_module_mapping")

if __name__ == "__main__":
    upgrade()
