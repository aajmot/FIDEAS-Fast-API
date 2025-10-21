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
                DO $$ BEGIN
                    CREATE TYPE result_type_enum AS ENUM ('Parametric', 'Image', 'Video', 'Both', 'Text', 'Others');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            session.execute(text("""
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
            """))
            
            session.execute(text("""
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
            """))
            
            session.execute(text("""
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
            """))
            
            session.commit()
            print("Migration 019 completed successfully")
            print("Created test_results table")
            print("Created test_result_details table")
            print("Created test_result_files table")
        except Exception as e:
            print(f"Migration 019 failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
