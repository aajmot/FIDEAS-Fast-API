#!/usr/bin/env python3
"""
Drop tenant_modules table (redundant with tenant_module_mapping)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Drop tenant_modules table if it exists"""
    print("Dropping tenant_modules table...")
    
    try:
        with db_manager.get_session() as session:
            session.execute(text("DROP TABLE IF EXISTS tenant_modules CASCADE"))
            session.commit()
            print("[OK] tenant_modules table dropped successfully")
            
    except Exception as e:
        print(f"[ERROR] Error dropping tenant_modules table: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running cleanup migration...")
    upgrade()
    print("Migration completed!")
