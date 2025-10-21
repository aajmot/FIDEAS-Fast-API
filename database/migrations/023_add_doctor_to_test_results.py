from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    """Add doctor_id and license_number columns to test_results table"""
    with db_manager.get_session() as session:
        # Add doctor_id column if not exists
        session.execute(text("""
            ALTER TABLE test_results 
            ADD COLUMN IF NOT EXISTS doctor_id INTEGER REFERENCES doctors(id)
        """))
        
        # Add license_number column if not exists
        session.execute(text("""
            ALTER TABLE test_results 
            ADD COLUMN IF NOT EXISTS license_number TEXT
        """))
        
        session.commit()
        print("Added doctor_id and license_number columns to test_results table")

def downgrade():
    """Remove doctor_id and license_number columns from test_results table"""
    with db_manager.get_session() as session:
        session.execute(text("""
            ALTER TABLE test_results 
            DROP COLUMN IF EXISTS doctor_id,
            DROP COLUMN IF EXISTS license_number
        """))
        
        session.commit()
        print("Removed doctor_id and license_number columns from test_results table")

if __name__ == "__main__":
    print("Running migration 023: Add doctor_id and license_number to test_results")
    upgrade()
    print("Migration 023 completed successfully")
