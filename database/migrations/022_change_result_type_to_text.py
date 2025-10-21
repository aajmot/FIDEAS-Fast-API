"""
Migration: Change result_type from enum to text in test_results table
"""

def upgrade(connection):
    """Change result_type column to text type"""
    cursor = connection.cursor()
    
    try:
        # Change column type from enum to text
        cursor.execute("""
            ALTER TABLE test_results 
            ALTER COLUMN result_type TYPE TEXT;
        """)
        
        # Drop the enum type if it exists
        cursor.execute("""
            DROP TYPE IF EXISTS resulttypeenum;
        """)
        
        connection.commit()
        print("Changed result_type to TEXT type in test_results table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error changing result_type column: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Revert result_type column to enum type"""
    cursor = connection.cursor()
    
    try:
        # Create enum type
        cursor.execute("""
            CREATE TYPE resulttypeenum AS ENUM ('PARAMETRIC', 'IMAGE', 'VIDEO', 'BOTH', 'TEXT', 'OTHERS');
        """)
        
        # Change column type back to enum
        cursor.execute("""
            ALTER TABLE test_results 
            ALTER COLUMN result_type TYPE resulttypeenum USING result_type::resulttypeenum;
        """)
        
        connection.commit()
        print("Reverted result_type to ENUM type in test_results table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error reverting result_type column: {str(e)}")
        raise
    finally:
        cursor.close()
