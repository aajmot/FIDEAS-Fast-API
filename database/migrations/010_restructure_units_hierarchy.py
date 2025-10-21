#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database import get_db_connection

def run_migration():
    """Restructure units table to use parent_id and remove subunit table"""
    print("Running migration 010: Restructure units hierarchy...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if subunit table exists and migrate data
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'subunit'
            );
        """)
        subunit_exists = cursor.fetchone()[0]
        
        if subunit_exists:
            print("Migrating data from subunit table...")
            
            # Get existing subunit data
            cursor.execute("""
                SELECT id, name, unit_id, tenant_id, created_at 
                FROM subunit
            """)
            subunits = cursor.fetchall()
            
            # Add parent_id column to units table if it doesn't exist
            cursor.execute("""
                ALTER TABLE units 
                ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES units(id) ON DELETE CASCADE
            """)
            
            # Add audit columns to units table if they don't exist
            cursor.execute("""
                ALTER TABLE units 
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE
            """)
            
            # Create trigger for updated_at
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            cursor.execute("""
                DROP TRIGGER IF EXISTS update_units_updated_at ON units;
                CREATE TRIGGER update_units_updated_at 
                    BEFORE UPDATE ON units 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """)
            
            # Insert subunits as child units
            for subunit in subunits:
                subunit_id, name, parent_unit_id, tenant_id, created_at = subunit
                cursor.execute("""
                    INSERT INTO units (name, parent_id, tenant_id, created_at, updated_at, is_deleted)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, parent_unit_id, tenant_id, created_at, created_at, False))
            
            # Drop subunit table
            cursor.execute("DROP TABLE IF EXISTS subunit CASCADE")
            print("Subunit table dropped and data migrated to units table")
        
        else:
            print("Subunit table doesn't exist, updating units table structure...")
            
            # Add parent_id column to units table if it doesn't exist
            cursor.execute("""
                ALTER TABLE units 
                ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES units(id) ON DELETE CASCADE
            """)
            
            # Add audit columns to units table if they don't exist
            cursor.execute("""
                ALTER TABLE units 
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE
            """)
            
            # Create trigger for updated_at
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            cursor.execute("""
                DROP TRIGGER IF EXISTS update_units_updated_at ON units;
                CREATE TRIGGER update_units_updated_at 
                    BEFORE UPDATE ON units 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """)
        
        # Update existing units to have updated_at if null
        cursor.execute("""
            UPDATE units 
            SET updated_at = created_at 
            WHERE updated_at IS NULL
        """)
        
        conn.commit()
        print("Migration 010 completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration 010 failed: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()