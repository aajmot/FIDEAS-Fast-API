"""
Migration: Add result_number to test_results table
"""

def upgrade(connection):
    """Add result_number column"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE test_results 
            ADD COLUMN IF NOT EXISTS result_number TEXT UNIQUE
        """)
        
        connection.commit()
        print("Added result_number column to test_results table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error adding column: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Remove result_number column"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE test_results 
            DROP COLUMN IF EXISTS result_number
        """)
        connection.commit()
        print("Removed result_number column from test_results table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error removing column: {str(e)}")
        raise
    finally:
        cursor.close()
