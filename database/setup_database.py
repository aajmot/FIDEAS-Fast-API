#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

def run_migrations():
    """Run database migration scripts in order"""
    print("Running database migrations...")
    
    migrations_dir = Path(__file__).parent / "migrations"
    
    # Import and run schema migration
    try:
        sys.path.insert(0, str(migrations_dir))
        import importlib.util
        
        # Load schema setup
        spec = importlib.util.spec_from_file_location("schema_setup", migrations_dir / "001_schema_setup.py")
        schema_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_module)
        schema_module.create_schema()
    except Exception as e:
        print(f"[ERROR] Schema migration failed: {str(e)}")
        raise
    
    # Import and run default data migration
    try:
        # Load default data
        spec = importlib.util.spec_from_file_location("default_data", migrations_dir / "002_default_data.py")
        data_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_module)
        data_module.insert_default_data()
    except Exception as e:
        print(f"[ERROR] Default data migration failed: {str(e)}")
        raise
    
    # Run additional migrations
    try:
        # Load is_tenant_admin migration
        spec = importlib.util.spec_from_file_location("migration_003", migrations_dir / "003_add_is_tenant_admin.py")
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        migration_module.upgrade()
    except Exception as e:
        # This migration might already be applied, so just log the warning
        print(f"[WARNING] Migration 003 failed (might already be applied): {str(e)}")
    
    # Run units restructure migration
    try:
        spec = importlib.util.spec_from_file_location("migration_009", migrations_dir / "009_restructure_units.py")
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        migration_module.run_migration()
    except Exception as e:
        print(f"[WARNING] Migration 009 failed (might already be applied): {str(e)}")
    
    # Run units hierarchy restructure migration
    try:
        spec = importlib.util.spec_from_file_location("migration_010", migrations_dir / "010_restructure_units_hierarchy.py")
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        migration_module.run_migration()
    except Exception as e:
        print(f"[WARNING] Migration 010 failed (might already be applied): {str(e)}")
def insert_account_master_data(tenant_id):
    """Insert default account groups and accounts for a specific tenant"""
    try:
        import importlib.util
        migrations_dir = Path(__file__).parent / "migrations"
        
        # Load default data module
        spec = importlib.util.spec_from_file_location("default_data", migrations_dir / "002_default_data.py")
        data_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_module)
        data_module.insert_account_master_data(tenant_id)
    except Exception as e:
        print(f"[ERROR] Error inserting account master data: {str(e)}")
        raise

def setup_database(verbose=True):
    """Main database setup function"""
    if verbose:
        print("=" * 50)
        print("FIDEAS Database Setup")
        print("=" * 50)
    
    try:
        # Run all migrations
        run_migrations()
        
        if verbose:
            print("=" * 50)
            print("[SUCCESS] Database setup completed successfully!")
            print("=" * 50)
            print("\nNext steps:")
            print("1. Run the application: python main.py")
            print("2. Complete tenant setup when prompted")
            print("3. Login with your admin credentials")
        
    except Exception as e:
        if verbose:
            print("=" * 50)
            print(f"[FAILED] Database setup failed: {str(e)}")
            print("=" * 50)
        raise  # Re-raise the exception instead of exiting

if __name__ == "__main__":
    try:
        setup_database(verbose=True)
    except Exception as e:
        print(f"[ERROR] Setup failed: {str(e)}")
        sys.exit(1)