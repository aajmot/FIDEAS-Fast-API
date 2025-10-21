#!/usr/bin/env python3
"""
Add Agencies Table Migration
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Create agencies table"""
    print("Creating agencies table...")
    
    try:
        with db_manager.get_session() as session:
            schema_sql = """
            CREATE TABLE IF NOT EXISTS agencies (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                name VARCHAR(200) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                address TEXT,
                tax_id VARCHAR(50),
                agency_type VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_by VARCHAR(100),
                is_delete BOOLEAN DEFAULT FALSE,
                CONSTRAINT unique_agency_phone_per_tenant UNIQUE (tenant_id, phone)
            );
            
            CREATE INDEX IF NOT EXISTS idx_agencies_tenant_id ON agencies(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_agencies_phone ON agencies(phone);
            """
            
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            for stmt in statements:
                if stmt:
                    session.execute(text(stmt))
            
            session.commit()
            print("[OK] Agencies table created successfully")
            
    except Exception as e:
        print(f"[ERROR] Error creating agencies table: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running agencies table migration...")
    upgrade()
    print("Migration completed!")
