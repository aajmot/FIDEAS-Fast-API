"""
Migration: Update agency_commissions table - replace test_id with product fields
"""

def upgrade(connection):
    """Update agency_commissions table"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE agency_commissions 
            DROP COLUMN IF EXISTS test_id,
            ADD COLUMN IF NOT EXISTS product_type TEXT NOT NULL DEFAULT 'Tests',
            ADD COLUMN IF NOT EXISTS product_id INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS product_name TEXT NOT NULL DEFAULT '',
            ADD COLUMN IF NOT EXISTS notes TEXT
        """)
        
        cursor.execute("""
            DROP INDEX IF EXISTS idx_agency_commissions_test
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agency_commissions_product ON agency_commissions(product_type, product_id)
        """)
        
        connection.commit()
        print("Updated agency_commissions table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error updating table: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Revert agency_commissions table changes"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE agency_commissions 
            DROP COLUMN IF EXISTS product_type,
            DROP COLUMN IF EXISTS product_id,
            DROP COLUMN IF EXISTS product_name,
            DROP COLUMN IF EXISTS notes,
            ADD COLUMN IF NOT EXISTS test_id INTEGER REFERENCES tests(id)
        """)
        
        connection.commit()
        print("Reverted agency_commissions table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error reverting table: {str(e)}")
        raise
    finally:
        cursor.close()
