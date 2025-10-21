"""
Migration: Restructure units table and remove subunits table
"""

import psycopg
from core.database.connection import db_manager
from core.shared.utils.logger import logger

def run_migration():
    """Restructure units table to include parent_id and remove subunits table"""
    
    migrations = [
        # Add new columns to units table
        """
        ALTER TABLE units 
        ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES units(id),
        ADD COLUMN IF NOT EXISTS conversion_factor DECIMAL(10,4) DEFAULT 1.0,
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
        """,
        
        # Migrate data from subunits to units as child records
        """
        INSERT INTO units (name, symbol, parent_id, conversion_factor, tenant_id, is_active, created_at, created_by, updated_by)
        SELECT 
            s.name,
            CONCAT(u.symbol, '-', s.name) as symbol,
            s.unit_id as parent_id,
            s.conversion_factor,
            s.tenant_id,
            s.is_active,
            s.created_at,
            s.created_by,
            s.updated_by
        FROM subunits s
        JOIN units u ON s.unit_id = u.id
        WHERE NOT EXISTS (
            SELECT 1 FROM units u2 
            WHERE u2.name = s.name AND u2.parent_id = s.unit_id
        );
        """,
        
        # Update products to use the migrated units instead of subunits
        """
        UPDATE products 
        SET unit_id = (
            SELECT u.id 
            FROM units u 
            JOIN subunits s ON u.name = s.name AND u.parent_id = s.unit_id
            WHERE s.id = products.subunit_id
        )
        WHERE subunit_id IS NOT NULL;
        """,
        
        # Remove subunit_id column from products
        """
        ALTER TABLE products DROP COLUMN IF EXISTS subunit_id;
        """,
        
        # Drop subunits table
        """
        DROP TABLE IF EXISTS subunits CASCADE;
        """,
        
        # Create index for parent_id
        """
        CREATE INDEX IF NOT EXISTS idx_units_parent_id ON units(parent_id);
        """,
        
        # Create index for updated_at
        """
        CREATE INDEX IF NOT EXISTS idx_units_updated_at ON units(updated_at);
        """
    ]
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                for migration in migrations:
                    logger.info(f"Executing: {migration.strip()[:50]}...")
                    cursor.execute(migration)
                
                conn.commit()
                logger.info("Migration 009 completed successfully")
                
    except Exception as e:
        logger.error(f"Migration 009 failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()