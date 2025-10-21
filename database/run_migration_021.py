#!/usr/bin/env python3
"""
Run migration 021: Add unit column to test_result_details
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
    """Execute migration 021"""
    print("Running migration 021: Add unit to test_result_details...")
    
    try:
        with db_manager.get_session() as session:
            # Add unit and notes columns
            session.execute(text("""
                ALTER TABLE test_result_details 
                ADD COLUMN IF NOT EXISTS unit TEXT;
            """))
            
            session.execute(text("""
                ALTER TABLE test_result_details 
                ADD COLUMN IF NOT EXISTS notes TEXT;
            """))
            
            session.commit()
            print("[OK] Migration 021 completed successfully")
            
    except Exception as e:
        print(f"[ERROR] Migration 021 failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
