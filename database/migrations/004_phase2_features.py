#!/usr/bin/env python3
"""
Phase 2 Features Migration
Adds cost centers, budgets, and integrations
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def run_migration():
    print("Running Phase 2 features migration...")
    
    try:
        with db_manager.get_session() as session:
            # Create cost_centers table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS cost_centers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    code VARCHAR(20) NOT NULL,
                    parent_id INTEGER REFERENCES cost_centers(id),
                    is_active BOOLEAN DEFAULT TRUE,
                    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_cost_center_code_tenant UNIQUE (code, tenant_id)
                )
            """))
            
            # Create budgets table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    fiscal_year_id INTEGER NOT NULL REFERENCES fiscal_years(id),
                    account_id INTEGER NOT NULL REFERENCES account_masters(id),
                    cost_center_id INTEGER REFERENCES cost_centers(id),
                    budget_amount NUMERIC(15, 2) NOT NULL,
                    actual_amount NUMERIC(15, 2) DEFAULT 0,
                    variance NUMERIC(15, 2) DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'DRAFT',
                    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(100),
                    CONSTRAINT uq_budget UNIQUE (fiscal_year_id, account_id, cost_center_id, tenant_id)
                )
            """))
            
            # Create integrations table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS integrations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    integration_type VARCHAR(50) NOT NULL,
                    provider VARCHAR(50) NOT NULL,
                    api_key VARCHAR(255),
                    api_secret VARCHAR(255),
                    webhook_url VARCHAR(255),
                    config TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_integration UNIQUE (integration_type, provider, tenant_id)
                )
            """))
            
            # Add cost_center_id to journal_details
            session.execute(text("""
                ALTER TABLE journal_details 
                ADD COLUMN IF NOT EXISTS cost_center_id INTEGER REFERENCES cost_centers(id)
            """))
            
            session.commit()
            print("[OK] Phase 2 features migration completed")
            
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
