"""
Migration: Add agency_commissions table
"""

def upgrade(connection):
    """Create agency_commissions table"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agency_commissions (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                agency_id INTEGER NOT NULL REFERENCES agencies(id),
                test_id INTEGER NOT NULL REFERENCES tests(id),
                commission_type TEXT,
                commission_value DECIMAL(10, 2),
                effective_from TIMESTAMP,
                effective_to TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agency_commissions_tenant ON agency_commissions(tenant_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agency_commissions_agency ON agency_commissions(agency_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agency_commissions_test ON agency_commissions(test_id);
        """)
        
        connection.commit()
        print("Created agency_commissions table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error creating table: {str(e)}")
        raise
    finally:
        cursor.close()

def downgrade(connection):
    """Drop agency_commissions table"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("DROP TABLE IF EXISTS agency_commissions")
        connection.commit()
        print("Dropped agency_commissions table")
        
    except Exception as e:
        connection.rollback()
        print(f"Error dropping table: {str(e)}")
        raise
    finally:
        cursor.close()
