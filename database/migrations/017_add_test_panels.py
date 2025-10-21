"""
Migration: Add test_panels and test_panel_items tables
"""

def upgrade(connection):
    """Create test_panels and test_panel_items tables"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_panels (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                name VARCHAR(200) NOT NULL,
                description TEXT,
                category_id INTEGER REFERENCES test_categories(id),
                cost DECIMAL(10, 2),
                gst DECIMAL(5, 2),
                cess DECIMAL(5, 2),
                expired_on TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_panel_items (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                panel_id INTEGER NOT NULL REFERENCES test_panels(id),
                test_id INTEGER NOT NULL REFERENCES tests(id),
                test_name VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        
        connection.commit()
        print("Created test_panels and test_panel_items tables")
        
    except Exception as e:
        connection.rollback()
        print(f"Error creating tables: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Drop test_panels and test_panel_items tables"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("DROP TABLE IF EXISTS test_panel_items")
        cursor.execute("DROP TABLE IF EXISTS test_panels")
        connection.commit()
        print("Dropped test_panels and test_panel_items tables")
        
    except Exception as e:
        connection.rollback()
        print(f"Error dropping tables: {str(e)}")
        raise
    finally:
        cursor.close()
