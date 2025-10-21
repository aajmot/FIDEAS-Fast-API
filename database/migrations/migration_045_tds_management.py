#!/usr/bin/env python3
"""
Migration 045: TDS Management
Creates TDS master table and menu entry
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def run_migration():
    """Add TDS management support"""
    print("Running Migration 045: TDS Management...")
    
    with db_manager.get_session() as session:
        try:
            # Create tds_sections table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS tds_sections (
                    id SERIAL PRIMARY KEY,
                    section_code VARCHAR(20) NOT NULL,
                    description TEXT NOT NULL,
                    rate DECIMAL(5,2) NOT NULL,
                    threshold_limit DECIMAL(15,2) DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    UNIQUE(section_code, tenant_id)
                )
            """))
            
            # Insert common TDS sections for all tenants
            session.execute(text("""
                INSERT INTO tds_sections (section_code, description, rate, threshold_limit, tenant_id)
                SELECT '194C', 'Payment to contractors', 1.00, 30000, id FROM tenants
                WHERE NOT EXISTS (
                    SELECT 1 FROM tds_sections WHERE section_code = '194C' AND tenant_id = tenants.id
                )
            """))
            
            session.execute(text("""
                INSERT INTO tds_sections (section_code, description, rate, threshold_limit, tenant_id)
                SELECT '194J', 'Professional or technical services', 10.00, 30000, id FROM tenants
                WHERE NOT EXISTS (
                    SELECT 1 FROM tds_sections WHERE section_code = '194J' AND tenant_id = tenants.id
                )
            """))
            
            # Add TDS menu entry
            session.execute(text("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order)
                SELECT 'TDS Management', 'TDS_MANAGEMENT', 'ACCOUNT', 
                    (SELECT id FROM menu_master WHERE menu_code = 'ACCOUNT_MASTER' LIMIT 1),
                    '💼', '/account/tds-management', 9
                WHERE NOT EXISTS (SELECT 1 FROM menu_master WHERE menu_code = 'TDS_MANAGEMENT')
            """))
            
            session.commit()
            print("[OK] Migration 045 completed successfully")
            
        except Exception as e:
            session.rollback()
            print(f"[ERROR] Migration 045 failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
