"""
Migration: Add commission_type and commission_value to tests table
"""

def upgrade(connection):
    """Add commission columns to tests table"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE tests 
            ADD COLUMN IF NOT EXISTS commission_type TEXT,
            ADD COLUMN IF NOT EXISTS commission_value DECIMAL(10, 2)
        """)
        
        connection.commit()
        print("Added commission_type and commission_value columns to tests table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error adding columns: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Remove commission columns from tests table"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE tests 
            DROP COLUMN IF EXISTS commission_type,
            DROP COLUMN IF EXISTS commission_value
        """)
        
        connection.commit()
        print("Removed commission_type and commission_value columns from tests table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error removing columns: {str(e)}")
        raise
    finally:
        cursor.close()
