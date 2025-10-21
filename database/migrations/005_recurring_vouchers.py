#!/usr/bin/env python3
"""
Recurring Vouchers Migration
Adds recurring_vouchers table
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def run_migration():
    print("Running recurring vouchers migration...")
    
    try:
        with db_manager.get_session() as session:
            # Create recurring_vouchers table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS recurring_vouchers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    voucher_type VARCHAR(50) NOT NULL,
                    frequency VARCHAR(20) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(100),
                    updated_at TIMESTAMP,
                    updated_by VARCHAR(100),
                    CONSTRAINT uq_recurring_voucher UNIQUE (name, tenant_id)
                )
            """))
            
            session.commit()
            print("[OK] Recurring vouchers migration completed")
            
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
