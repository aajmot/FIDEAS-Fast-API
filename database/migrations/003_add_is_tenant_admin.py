"""
Migration: Add is_tenant_admin field to users table
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    """Add is_tenant_admin column to users table"""
    with db_manager.get_session() as session:
        try:
            # Add the is_tenant_admin column
            session.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_tenant_admin BOOLEAN DEFAULT FALSE
            """))
            
            session.commit()
            print("Added is_tenant_admin column to users table")
            
        except Exception as e:
            session.rollback()
            print(f"Failed to add is_tenant_admin column: {str(e)}")
            raise

def downgrade():
    """Remove is_tenant_admin column from users table"""
    with db_manager.get_session() as session:
        try:
            # Remove the is_tenant_admin column
            session.execute(text("""
                ALTER TABLE users 
                DROP COLUMN IF EXISTS is_tenant_admin
            """))
            
            session.commit()
            print("Removed is_tenant_admin column from users table")
            
        except Exception as e:
            session.rollback()
            print(f"Failed to remove is_tenant_admin column: {str(e)}")
            raise

if __name__ == "__main__":
    print("Running migration: Add is_tenant_admin field to users table")
    upgrade()
    print("Migration completed successfully")