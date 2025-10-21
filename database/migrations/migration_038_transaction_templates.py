#!/usr/bin/env python3
"""
Migration 038: Create transaction templates for rule-based posting
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Create transaction template tables"""
    print("Running migration 038...")
    
    with db_manager.get_session() as session:
        # Create transaction_templates table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS transaction_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) NOT NULL,
                transaction_type VARCHAR(50) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP,
                updated_by VARCHAR(100),
                UNIQUE(code, tenant_id)
            )
        """))
        
        # Create transaction_template_rules table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS transaction_template_rules (
                id SERIAL PRIMARY KEY,
                template_id INTEGER NOT NULL REFERENCES transaction_templates(id) ON DELETE CASCADE,
                line_number INTEGER NOT NULL,
                account_id INTEGER REFERENCES account_masters(id),
                account_type VARCHAR(50),
                entry_type VARCHAR(10) NOT NULL,
                amount_source VARCHAR(50) NOT NULL,
                percentage NUMERIC(5, 2),
                narration TEXT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(template_id, line_number)
            )
        """))
        
        # Insert default templates for each transaction type
        session.execute(text("""
            INSERT INTO transaction_templates (name, code, transaction_type, description, tenant_id, created_by)
            SELECT 
                'Sales Order Posting',
                'SO_POST',
                'SALES_ORDER',
                'Default posting template for sales orders',
                t.id,
                'system'
            FROM tenants t
            WHERE NOT EXISTS (
                SELECT 1 FROM transaction_templates tt 
                WHERE tt.code = 'SO_POST' AND tt.tenant_id = t.id
            )
        """))
        
        session.execute(text("""
            INSERT INTO transaction_templates (name, code, transaction_type, description, tenant_id, created_by)
            SELECT 
                'Purchase Order Posting',
                'PO_POST',
                'PURCHASE_ORDER',
                'Default posting template for purchase orders',
                t.id,
                'system'
            FROM tenants t
            WHERE NOT EXISTS (
                SELECT 1 FROM transaction_templates tt 
                WHERE tt.code = 'PO_POST' AND tt.tenant_id = t.id
            )
        """))
        
        session.execute(text("""
            INSERT INTO transaction_templates (name, code, transaction_type, description, tenant_id, created_by)
            SELECT 
                'Prescription Posting',
                'RX_POST',
                'PRESCRIPTION',
                'Default posting template for prescriptions',
                t.id,
                'system'
            FROM tenants t
            WHERE NOT EXISTS (
                SELECT 1 FROM transaction_templates tt 
                WHERE tt.code = 'RX_POST' AND tt.tenant_id = t.id
            )
        """))
        
        session.execute(text("""
            INSERT INTO transaction_templates (name, code, transaction_type, description, tenant_id, created_by)
            SELECT 
                'Diagnostic Sales Posting',
                'DIAG_POST',
                'DIAGNOSTIC_SALES',
                'Default posting template for diagnostic sales',
                t.id,
                'system'
            FROM tenants t
            WHERE NOT EXISTS (
                SELECT 1 FROM transaction_templates tt 
                WHERE tt.code = 'DIAG_POST' AND tt.tenant_id = t.id
            )
        """))
        
        # Insert default rules for Sales Order
        session.execute(text("""
            INSERT INTO transaction_template_rules 
            (template_id, line_number, account_type, entry_type, amount_source, narration, tenant_id)
            SELECT 
                tt.id,
                1,
                'ACCOUNTS_RECEIVABLE',
                'DEBIT',
                'TOTAL_AMOUNT',
                'Sales to customer',
                tt.tenant_id
            FROM transaction_templates tt
            WHERE tt.code = 'SO_POST'
            AND NOT EXISTS (
                SELECT 1 FROM transaction_template_rules ttr 
                WHERE ttr.template_id = tt.id AND ttr.line_number = 1
            )
        """))
        
        session.execute(text("""
            INSERT INTO transaction_template_rules 
            (template_id, line_number, account_type, entry_type, amount_source, narration, tenant_id)
            SELECT 
                tt.id,
                2,
                'SALES_REVENUE',
                'CREDIT',
                'TOTAL_AMOUNT',
                'Sales revenue',
                tt.tenant_id
            FROM transaction_templates tt
            WHERE tt.code = 'SO_POST'
            AND NOT EXISTS (
                SELECT 1 FROM transaction_template_rules ttr 
                WHERE ttr.template_id = tt.id AND ttr.line_number = 2
            )
        """))
        
        # Insert default rules for Purchase Order
        session.execute(text("""
            INSERT INTO transaction_template_rules 
            (template_id, line_number, account_type, entry_type, amount_source, narration, tenant_id)
            SELECT 
                tt.id,
                1,
                'INVENTORY',
                'DEBIT',
                'TOTAL_AMOUNT',
                'Purchase of goods',
                tt.tenant_id
            FROM transaction_templates tt
            WHERE tt.code = 'PO_POST'
            AND NOT EXISTS (
                SELECT 1 FROM transaction_template_rules ttr 
                WHERE ttr.template_id = tt.id AND ttr.line_number = 1
            )
        """))
        
        session.execute(text("""
            INSERT INTO transaction_template_rules 
            (template_id, line_number, account_type, entry_type, amount_source, narration, tenant_id)
            SELECT 
                tt.id,
                2,
                'ACCOUNTS_PAYABLE',
                'CREDIT',
                'TOTAL_AMOUNT',
                'Purchase from supplier',
                tt.tenant_id
            FROM transaction_templates tt
            WHERE tt.code = 'PO_POST'
            AND NOT EXISTS (
                SELECT 1 FROM transaction_template_rules ttr 
                WHERE ttr.template_id = tt.id AND ttr.line_number = 2
            )
        """))
        
        # Insert default rules for Prescription
        session.execute(text("""
            INSERT INTO transaction_template_rules 
            (template_id, line_number, account_type, entry_type, amount_source, narration, tenant_id)
            SELECT 
                tt.id,
                1,
                'ACCOUNTS_RECEIVABLE',
                'DEBIT',
                'TOTAL_AMOUNT',
                'Prescription sales',
                tt.tenant_id
            FROM transaction_templates tt
            WHERE tt.code = 'RX_POST'
            AND NOT EXISTS (
                SELECT 1 FROM transaction_template_rules ttr 
                WHERE ttr.template_id = tt.id AND ttr.line_number = 1
            )
        """))
        
        session.execute(text("""
            INSERT INTO transaction_template_rules 
            (template_id, line_number, account_type, entry_type, amount_source, narration, tenant_id)
            SELECT 
                tt.id,
                2,
                'PHARMACY_REVENUE',
                'CREDIT',
                'TOTAL_AMOUNT',
                'Pharmacy revenue',
                tt.tenant_id
            FROM transaction_templates tt
            WHERE tt.code = 'RX_POST'
            AND NOT EXISTS (
                SELECT 1 FROM transaction_template_rules ttr 
                WHERE ttr.template_id = tt.id AND ttr.line_number = 2
            )
        """))
        
        # Insert default rules for Diagnostic Sales
        session.execute(text("""
            INSERT INTO transaction_template_rules 
            (template_id, line_number, account_type, entry_type, amount_source, narration, tenant_id)
            SELECT 
                tt.id,
                1,
                'ACCOUNTS_RECEIVABLE',
                'DEBIT',
                'TOTAL_AMOUNT',
                'Diagnostic test charges',
                tt.tenant_id
            FROM transaction_templates tt
            WHERE tt.code = 'DIAG_POST'
            AND NOT EXISTS (
                SELECT 1 FROM transaction_template_rules ttr 
                WHERE ttr.template_id = tt.id AND ttr.line_number = 1
            )
        """))
        
        session.execute(text("""
            INSERT INTO transaction_template_rules 
            (template_id, line_number, account_type, entry_type, amount_source, narration, tenant_id)
            SELECT 
                tt.id,
                2,
                'DIAGNOSTIC_REVENUE',
                'CREDIT',
                'TOTAL_AMOUNT',
                'Diagnostic revenue',
                tt.tenant_id
            FROM transaction_templates tt
            WHERE tt.code = 'DIAG_POST'
            AND NOT EXISTS (
                SELECT 1 FROM transaction_template_rules ttr 
                WHERE ttr.template_id = tt.id AND ttr.line_number = 2
            )
        """))
        
        session.commit()
        print("[OK] Migration 038 completed")

def downgrade():
    """Remove transaction template tables"""
    print("Rolling back migration 038...")
    
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS transaction_template_rules"))
        session.execute(text("DROP TABLE IF EXISTS transaction_templates"))
        session.commit()
        print("[OK] Migration 038 rolled back")

if __name__ == "__main__":
    upgrade()
