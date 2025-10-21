#!/usr/bin/env python3
"""
Add product_rate column to agency_commissions table
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add product_rate column"""
    print("Adding product_rate column to agency_commissions table...")
    
    try:
        with db_manager.get_session() as session:
            session.execute(text(
                "ALTER TABLE agency_commissions ADD COLUMN product_rate DECIMAL(10,2)"
            ))
            session.commit()
            print("[OK] product_rate column added")
            
    except Exception as e:
        print(f"[ERROR] Error adding column: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running migration 032...")
    upgrade()
    print("Migration 032 completed!")
