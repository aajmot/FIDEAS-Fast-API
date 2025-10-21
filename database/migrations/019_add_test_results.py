"""
Migration: Add test_results, test_result_details, and test_result_files tables
"""

def upgrade(connection):
    """Create test results tables"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            DO $$ BEGIN
                CREATE TYPE result_type_enum AS ENUM ('Parametric', 'Image', 'Video', 'Both', 'Text', 'Others');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                test_order_id INTEGER NOT NULL REFERENCES test_orders(id),
                result_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                overall_report TEXT,
                performed_by TEXT,
                result_type result_type_enum,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_result_details (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                test_result_id INTEGER NOT NULL REFERENCES test_results(id),
                parameter_id TEXT,
                parameter_name TEXT,
                parameter_value TEXT,
                reference_value TEXT,
                verdict TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_result_files (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                test_result_id INTEGER NOT NULL REFERENCES test_results(id),
                file_name TEXT,
                file_path TEXT,
                file_format TEXT,
                file_size BIGINT,
                acquisition_date TIMESTAMP,
                description TEXT,
                storage_system TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        
        connection.commit()
        print("Created test_results, test_result_details, and test_result_files tables")
        
    except Exception as e:
        connection.rollback()
        print(f"Error creating tables: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Drop test results tables"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("DROP TABLE IF EXISTS test_result_files")
        cursor.execute("DROP TABLE IF EXISTS test_result_details")
        cursor.execute("DROP TABLE IF EXISTS test_results")
        cursor.execute("DROP TYPE IF EXISTS result_type_enum")
        connection.commit()
        print("Dropped test results tables")
        
    except Exception as e:
        connection.rollback()
        print(f"Error dropping tables: {str(e)}")
        raise
    finally:
        cursor.close()
