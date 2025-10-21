"""
Migration: Add tenant_id to units and other missing tables
"""

import psycopg
from core.database.connection import db_manager
from core.shared.utils.logger import logger

def run_migration():
    """Add tenant_id column to units and other tables that need it"""
    
    migrations = [
        # Add tenant_id to units table
        """
        ALTER TABLE units 
        ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id);
        """,
        
        # Add created_by and updated_by to units table
        """
        ALTER TABLE units 
        ADD COLUMN IF NOT EXISTS created_by VARCHAR(100),
        ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100);
        """,
        
        # Add tenant_id to subunits table if it doesn't exist
        """
        ALTER TABLE subunits 
        ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id);
        """,
        
        # Add created_by and updated_by to subunits table
        """
        ALTER TABLE subunits 
        ADD COLUMN IF NOT EXISTS created_by VARCHAR(100),
        ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100);
        """,
        
        # Update existing units to have tenant_id = 1 (default tenant)
        """
        UPDATE units SET tenant_id = 1 WHERE tenant_id IS NULL;
        """,
        
        # Update existing subunits to have tenant_id = 1 (default tenant)
        """
        UPDATE subunits SET tenant_id = 1 WHERE tenant_id IS NULL;
        """,
        
        # Make tenant_id NOT NULL after setting default values
        """
        ALTER TABLE units ALTER COLUMN tenant_id SET NOT NULL;
        """,
        
        """
        ALTER TABLE subunits ALTER COLUMN tenant_id SET NOT NULL;
        """
    ]
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                for migration in migrations:
                    logger.info(f"Executing: {migration.strip()[:50]}...")
                    cursor.execute(migration)
                
                conn.commit()
                logger.info("Migration 008 completed successfully")
                
    except Exception as e:
        logger.error(f"Migration 008 failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()