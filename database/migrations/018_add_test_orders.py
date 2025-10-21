"""
Migration: Add test_orders and test_order_items tables
"""

def upgrade(connection):
    """Create test_orders and test_order_items tables"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_orders (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                test_order_number TEXT UNIQUE NOT NULL,
                appointment_id INTEGER REFERENCES appointments(id),
                patient_name VARCHAR(200),
                patient_phone VARCHAR(20),
                doctor_name VARCHAR(200),
                doctor_phone VARCHAR(20),
                doctor_license_number VARCHAR(100),
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                urgency TEXT,
                notes TEXT,
                agency_id INTEGER REFERENCES agencies(id),
                total_amount DECIMAL(10, 2),
                disc_percentage DECIMAL(5, 2),
                disc_amount DECIMAL(10, 2),
                roundoff DECIMAL(10, 2),
                final_amount DECIMAL(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_order_items (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                test_order_id INTEGER NOT NULL REFERENCES test_orders(id),
                test_id INTEGER REFERENCES tests(id),
                test_name VARCHAR(200),
                panel_id INTEGER REFERENCES test_panels(id),
                panel_name VARCHAR(200),
                rate DECIMAL(10, 2),
                gst DECIMAL(5, 2),
                cess DECIMAL(5, 2),
                disc_percentage DECIMAL(5, 2),
                disc_amount DECIMAL(10, 2),
                total_amount DECIMAL(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        
        connection.commit()
        print("Created test_orders and test_order_items tables")
        
    except Exception as e:
        connection.rollback()
        print(f"Error creating tables: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Drop test_orders and test_order_items tables"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("DROP TABLE IF EXISTS test_order_items")
        cursor.execute("DROP TABLE IF EXISTS test_orders")
        connection.commit()
        print("Dropped test_orders and test_order_items tables")
        
    except Exception as e:
        connection.rollback()
        print(f"Error dropping tables: {str(e)}")
        raise
    finally:
        cursor.close()
