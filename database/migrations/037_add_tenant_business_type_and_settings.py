#!/usr/bin/env python3
"""
Migration 037: Add tenant business_type and tenant_settings table
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add business_type to tenants and create tenant_settings table"""
    print("Running migration 037...")
    
    with db_manager.get_session() as session:
        # Add business_type column to tenants table
        session.execute(text("""
            ALTER TABLE tenants 
            ADD COLUMN IF NOT EXISTS business_type VARCHAR(20) DEFAULT 'TRADING'
        """))
        
        # Create tenant_settings table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS tenant_settings (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                setting VARCHAR(100) NOT NULL,
                description TEXT,
                value_type VARCHAR(20) NOT NULL DEFAULT 'BOOLEAN',
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP,
                updated_by VARCHAR(100),
                UNIQUE(tenant_id, setting)
            )
        """))
        
        # Insert default settings for existing tenants
        session.execute(text("""
            INSERT INTO tenant_settings (tenant_id, setting, description, value_type, value, created_by)
            SELECT 
                t.id,
                'enable_inventory',
                'Enable inventory management features',
                'BOOLEAN',
                CASE WHEN t.business_type = 'SERVICE' THEN 'FALSE' ELSE 'TRUE' END,
                'system'
            FROM tenants t
            WHERE NOT EXISTS (
                SELECT 1 FROM tenant_settings ts 
                WHERE ts.tenant_id = t.id AND ts.setting = 'enable_inventory'
            )
        """))
        
        session.execute(text("""
            INSERT INTO tenant_settings (tenant_id, setting, description, value_type, value, created_by)
            SELECT 
                t.id,
                'enable_gst',
                'Enable GST/tax management',
                'BOOLEAN',
                'TRUE',
                'system'
            FROM tenants t
            WHERE NOT EXISTS (
                SELECT 1 FROM tenant_settings ts 
                WHERE ts.tenant_id = t.id AND ts.setting = 'enable_gst'
            )
        """))
        
        session.execute(text("""
            INSERT INTO tenant_settings (tenant_id, setting, description, value_type, value, created_by)
            SELECT 
                t.id,
                'enable_bank_entry',
                'Enable bank reconciliation features',
                'BOOLEAN',
                'TRUE',
                'system'
            FROM tenants t
            WHERE NOT EXISTS (
                SELECT 1 FROM tenant_settings ts 
                WHERE ts.tenant_id = t.id AND ts.setting = 'enable_bank_entry'
            )
        """))
        
        session.commit()
        print("[OK] Migration 037 completed")

def downgrade():
    """Remove tenant_settings table and business_type column"""
    print("Rolling back migration 037...")
    
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS tenant_settings"))
        session.execute(text("ALTER TABLE tenants DROP COLUMN IF EXISTS business_type"))
        session.commit()
        print("[OK] Migration 037 rolled back")

if __name__ == "__main__":
    upgrade()
