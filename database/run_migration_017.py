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
            """))
            
            session.execute(text("""
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
            """))
            
            session.commit()
            print("Migration 017 completed successfully")
            print("Created test_panels table")
            print("Created test_panel_items table")
        except Exception as e:
            print(f"Migration 017 failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
