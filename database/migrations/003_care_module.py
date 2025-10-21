import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from core.database.connection import db_manager

def create_care_tables():
    """Create care module tables"""
    with db_manager.get_session() as session:
        # Create test_categories table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS test_categories (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                name VARCHAR(200) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """))
        
        # Create tests table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS tests (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                name VARCHAR(200) NOT NULL,
                category_id INTEGER REFERENCES test_categories(id),
                body_part VARCHAR(100),
                description TEXT,
                typical_duration VARCHAR(50),
                preparation_instruction TEXT,
                rate DECIMAL(10, 2),
                hsn_code VARCHAR(20),
                gst DECIMAL(5, 2),
                cess DECIMAL(5, 2),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """))
        
        # Create test_parameters table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS test_parameters (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                test_id INTEGER NOT NULL REFERENCES tests(id),
                name VARCHAR(200) NOT NULL,
                unit VARCHAR(50),
                normal_range VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """))
        
        session.commit()
        print("✓ Care module tables created successfully")

if __name__ == "__main__":
    create_care_tables()
