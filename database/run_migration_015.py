#!/usr/bin/env python3

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from core.database.connection import db_manager
import importlib.util

def run_migration():
    print("=" * 60)
    print("Running Migration 015: Add audit fields to prescription_items")
    print("=" * 60)
    
    try:
        conn = db_manager._engine.raw_connection()
        
        migrations_dir = Path(__file__).parent / "migrations"
        spec = importlib.util.spec_from_file_location(
            "migration_015", 
            migrations_dir / "015_add_prescription_items_audit_fields.py"
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        
        migration.upgrade(conn)
        conn.close()
        
        print("=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print("=" * 60)
        print(f"Migration failed: {str(e)}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
