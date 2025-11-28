"""
Database initialization utility for ensuring all tables exist and initial data is loaded
"""

import os
import sys
from pathlib import Path
from sqlalchemy import text, inspect
from core.database.connection import db_manager, Base
from core.shared.utils.logger import logger

def ensure_database_initialized():
    """
    Ensure all required tables exist and initial data is loaded.
    This should be called during tenant registration.
    """
    try:
        with db_manager.get_session() as session:
            # Check if core tables exist
            inspector = inspect(session.bind)
            existing_tables = inspector.get_table_names()
            
            # Required core tables
            required_tables = [
                'tenants', 'users', 'roles', 'user_roles', 'legal_entities',
                'financial_years', 'module_master', 'tenant_module_mapping',
                'menu_master', 'role_menu_mapping'
            ]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logger.info(f"Missing tables detected: {missing_tables}. Running database setup...", "DatabaseInitializer")
                _run_database_setup()
            else:
                logger.info("All core tables exist", "DatabaseInitializer")
                
            # Ensure default data exists
            _ensure_default_data_exists(session)
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", "DatabaseInitializer")
        raise

def _run_database_setup():
    """Run the complete database setup including migrations"""
    try:
        # Import all models to ensure they're registered with SQLAlchemy
        import modules.admin_module.models.entities
        import modules.account_module.models.entities
        import modules.account_module.models.bank_account_entity
        import modules.inventory_module.models.entities
        import modules.clinic_module.models.entities
        
        # Use SQLAlchemy to create all tables
        from core.database.connection import db_manager
        db_manager.create_tables()
        logger.info("Database tables created", "DatabaseInitializer")
        
        # Insert default data
        _insert_default_data()
        logger.info("Database setup completed", "DatabaseInitializer")
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}", "DatabaseInitializer")
        raise

def _ensure_default_data_exists(session):
    """Ensure default data exists in core tables"""
    try:
        # Check if module_master has data
        result = session.execute(text("SELECT COUNT(*) FROM module_master"))
        module_count = result.scalar()
        
        if module_count == 0:
            logger.info("No default data found. Inserting default data...", "DatabaseInitializer")
            _insert_default_data()
        else:
            logger.info("Default data exists", "DatabaseInitializer")
            
    except Exception as e:
        logger.error(f"Failed to check/insert default data: {str(e)}", "DatabaseInitializer")
        raise

def _insert_default_data():
    """Insert default data using the migration script"""
    try:
        import importlib.util
        migrations_dir = Path(__file__).parent.parent.parent.parent / "database" / "migrations"
        
        # Load default data module
        spec = importlib.util.spec_from_file_location("default_data", migrations_dir / "002_default_data.py")
        data_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_module)
        data_module.insert_default_data()
        
        logger.info("Default data inserted successfully", "DatabaseInitializer")
    except Exception as e:
        logger.error(f"Failed to insert default data: {str(e)}", "DatabaseInitializer")
        raise

def initialize_tenant_data(tenant_id):
    """Initialize tenant-specific data after tenant creation"""
    try:
        from database.setup_database import insert_account_master_data
        insert_account_master_data(tenant_id)
        logger.info(f"Tenant data initialized for tenant_id: {tenant_id}", "DatabaseInitializer")
    except Exception as e:
        logger.error(f"Failed to initialize tenant data: {str(e)}", "DatabaseInitializer")
        raise