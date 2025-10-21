"""
Migration: Add audit fields to prescription_items table
"""

def upgrade(connection):
    """Add product_name and audit fields to prescription_items"""
    cursor = connection.cursor()
    
    try:
        # Add product_name column
        cursor.execute("""
            ALTER TABLE prescription_items 
            ADD COLUMN IF NOT EXISTS product_name VARCHAR(200)
        """)
        
        # Add audit columns
        cursor.execute("""
            ALTER TABLE prescription_items 
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ADD COLUMN IF NOT EXISTS created_by VARCHAR(100),
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100),
            ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE
        """)
        
        connection.commit()
        print("Added audit fields to prescription_items table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error adding audit fields to prescription_items: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Remove audit fields from prescription_items"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE prescription_items 
            DROP COLUMN IF EXISTS product_name,
            DROP COLUMN IF EXISTS created_at,
            DROP COLUMN IF EXISTS created_by,
            DROP COLUMN IF EXISTS updated_at,
            DROP COLUMN IF EXISTS updated_by,
            DROP COLUMN IF EXISTS is_deleted
        """)
        
        connection.commit()
        print("Removed audit fields from prescription_items table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error removing audit fields from prescription_items: {str(e)}")
        raise
    finally:
        cursor.close()
