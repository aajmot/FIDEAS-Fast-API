#!/usr/bin/env python3
"""
Add agency_id to appointments table
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    print("Adding agency_id to appointments table...")
    
    try:
        with db_manager.get_session() as session:
            session.execute(text("""
                ALTER TABLE appointments 
                ADD COLUMN IF NOT EXISTS agency_id INTEGER REFERENCES agencies(id);
            """))
            
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appointments_agency ON appointments(agency_id);
            """))
            
            session.commit()
            print("[OK] Added agency_id to appointments table")
            
    except Exception as e:
        print(f"[ERROR] Error adding agency_id: {str(e)}")
        raise

if __name__ == "__main__":
    upgrade()
