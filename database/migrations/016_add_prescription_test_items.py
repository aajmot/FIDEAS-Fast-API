"""
Migration: Add prescription_test_items table
"""

def upgrade(connection):
    """Create prescription_test_items table"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prescription_test_items (
                id SERIAL PRIMARY KEY,
                prescription_id INTEGER NOT NULL REFERENCES prescriptions(id),
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                test_id INTEGER NOT NULL REFERENCES tests(id),
                test_name VARCHAR(200),
                instructions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        
        connection.commit()
        print("Created prescription_test_items table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error creating prescription_test_items table: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Drop prescription_test_items table"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("DROP TABLE IF EXISTS prescription_test_items")
        connection.commit()
        print("Dropped prescription_test_items table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error dropping prescription_test_items table: {str(e)}")
        raise
    finally:
        cursor.close()
