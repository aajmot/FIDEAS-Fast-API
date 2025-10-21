#!/usr/bin/env python3
"""
Run migration 022: Change result_type to text
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def run_migration():
    """Execute migration 022"""
    print("Running migration 022: Change result_type to text...")
    
    try:
        with db_manager.get_session() as session:
            # Change column type from enum to text
            session.execute(text("""
                ALTER TABLE test_results 
                ALTER COLUMN result_type TYPE TEXT;
            """))
            
            # Drop the enum type if it exists
            session.execute(text("""
                DROP TYPE IF EXISTS resulttypeenum;
            """))
            
            session.commit()
            print("[OK] Migration 022 completed successfully")
            
    except Exception as e:
        print(f"[ERROR] Migration 022 failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
