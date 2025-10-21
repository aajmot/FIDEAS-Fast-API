#!/usr/bin/env python3
"""
Add Notes Column to Order Commissions Table
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def add_notes_column():
    """Add notes column to order_commissions table"""
    print("Adding notes column to order_commissions table...")
    
    try:
        with db_manager.get_session() as session:
            session.execute(text("""
                ALTER TABLE order_commissions 
                ADD COLUMN IF NOT EXISTS notes TEXT
            """))
            
            session.commit()
            print("[OK] Notes column added successfully")
            
    except Exception as e:
        print(f"[ERROR] Error adding notes column: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running add notes column migration...")
    add_notes_column()
    print("Migration completed!")
