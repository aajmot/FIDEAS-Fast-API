import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def run_migration():
    with db_manager.get_session() as session:
        try:
            session.execute(text("""
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
            """))
            
            session.execute(text("""
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
            """))
            
            session.commit()
            print("Migration 018 completed successfully")
            print("Created test_orders table")
            print("Created test_order_items table")
        except Exception as e:
            print(f"Migration 018 failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
