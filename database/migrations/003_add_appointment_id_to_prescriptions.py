#!/usr/bin/env python3
"""
Migration: Add appointment_id to prescriptions table
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def run_migration():
    """Add appointment_id column to prescriptions table"""
    try:
        with db_manager.get_session() as session:
            # Add appointment_id column to prescriptions table
            session.execute(text("""
                ALTER TABLE prescriptions 
                ADD COLUMN IF NOT EXISTS appointment_id INTEGER REFERENCES appointments(id)
            """))
            
            session.commit()
            print("[OK] Added appointment_id column to prescriptions table")
            
    except Exception as e:
        print(f"[ERROR] Error in migration: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running prescription appointment_id migration...")
    run_migration()
    print("Migration completed!")