"""
Migration: Add unit column to test_result_details table
"""

def upgrade(connection):
    """Add unit column to test_result_details"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE test_result_details 
            ADD COLUMN IF NOT EXISTS unit TEXT;
        """)
        
        cursor.execute("""
            ALTER TABLE test_result_details 
            ADD COLUMN IF NOT EXISTS notes TEXT;
        """)
        
        connection.commit()
        print("Added unit and notes columns to test_result_details table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error adding unit column: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Remove unit column from test_result_details"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE test_result_details 
            DROP COLUMN IF EXISTS unit;
        """)
        
        cursor.execute("""
            ALTER TABLE test_result_details 
            DROP COLUMN IF EXISTS notes;
        """)
        
        connection.commit()
        print("Removed unit and notes columns from test_result_details table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error removing unit column: {str(e)}")
        raise
    finally:
        cursor.close()
