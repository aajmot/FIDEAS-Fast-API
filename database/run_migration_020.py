import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def run_migration():
    with db_manager.get_session() as session:
        try:
            session.execute(text("""
                ALTER TABLE test_results 
                ADD COLUMN IF NOT EXISTS result_number TEXT UNIQUE
            """))
            
            session.commit()
            print("Migration 020 completed successfully")
            print("Added result_number column to test_results table")
        except Exception as e:
            print(f"Migration 020 failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
