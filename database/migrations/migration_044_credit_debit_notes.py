#!/usr/bin/env python3
"""
Migration 044: Credit and Debit Notes
Creates tables and menu entries for credit/debit notes
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def run_migration():
    """Add credit and debit notes support"""
    print("Running Migration 044: Credit and Debit Notes...")
    
    with db_manager.get_session() as session:
        try:
            # Create credit_notes table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS credit_notes (
                    id SERIAL PRIMARY KEY,
                    note_number VARCHAR(50) NOT NULL,
                    note_date DATE NOT NULL,
                    customer_id INTEGER REFERENCES customers(id),
                    original_invoice_id INTEGER,
                    original_invoice_number VARCHAR(50),
                    reason TEXT,
                    subtotal DECIMAL(15,2) DEFAULT 0,
                    tax_amount DECIMAL(15,2) DEFAULT 0,
                    total_amount DECIMAL(15,2) NOT NULL,
                    voucher_id INTEGER REFERENCES vouchers(id),
                    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(100),
                    updated_at TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    UNIQUE(note_number, tenant_id)
                )
            """))
            
            # Create credit_note_items table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS credit_note_items (
                    id SERIAL PRIMARY KEY,
                    credit_note_id INTEGER NOT NULL REFERENCES credit_notes(id) ON DELETE CASCADE,
                    product_id INTEGER REFERENCES products(id),
                    description TEXT,
                    quantity DECIMAL(15,3) NOT NULL,
                    rate DECIMAL(15,2) NOT NULL,
                    tax_rate DECIMAL(5,2) DEFAULT 0,
                    tax_amount DECIMAL(15,2) DEFAULT 0,
                    amount DECIMAL(15,2) NOT NULL,
                    tenant_id INTEGER NOT NULL REFERENCES tenants(id)
                )
            """))
            
            # Create debit_notes table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS debit_notes (
                    id SERIAL PRIMARY KEY,
                    note_number VARCHAR(50) NOT NULL,
                    note_date DATE NOT NULL,
                    supplier_id INTEGER REFERENCES suppliers(id),
                    original_invoice_id INTEGER,
                    original_invoice_number VARCHAR(50),
                    reason TEXT,
                    subtotal DECIMAL(15,2) DEFAULT 0,
                    tax_amount DECIMAL(15,2) DEFAULT 0,
                    total_amount DECIMAL(15,2) NOT NULL,
                    voucher_id INTEGER REFERENCES vouchers(id),
                    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(100),
                    updated_at TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    UNIQUE(note_number, tenant_id)
                )
            """))
            
            # Create debit_note_items table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS debit_note_items (
                    id SERIAL PRIMARY KEY,
                    debit_note_id INTEGER NOT NULL REFERENCES debit_notes(id) ON DELETE CASCADE,
                    product_id INTEGER REFERENCES products(id),
                    description TEXT,
                    quantity DECIMAL(15,3) NOT NULL,
                    rate DECIMAL(15,2) NOT NULL,
                    tax_rate DECIMAL(5,2) DEFAULT 0,
                    tax_amount DECIMAL(15,2) DEFAULT 0,
                    amount DECIMAL(15,2) NOT NULL,
                    tenant_id INTEGER NOT NULL REFERENCES tenants(id)
                )
            """))
            
            # Add voucher types
            session.execute(text("""
                INSERT INTO voucher_types (name, code, prefix, tenant_id, is_active)
                SELECT 'Credit Note', 'CN', 'CN-', id, true
                FROM tenants
                WHERE NOT EXISTS (
                    SELECT 1 FROM voucher_types 
                    WHERE code = 'CN' AND tenant_id = tenants.id
                )
            """))
            
            session.execute(text("""
                INSERT INTO voucher_types (name, code, prefix, tenant_id, is_active)
                SELECT 'Debit Note', 'DN', 'DN-', id, true
                FROM tenants
                WHERE NOT EXISTS (
                    SELECT 1 FROM voucher_types 
                    WHERE code = 'DN' AND tenant_id = tenants.id
                )
            """))
            
            # Add menu entries
            session.execute(text("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order)
                SELECT 'Credit Note', 'CREDIT_NOTE', 'ACCOUNT', 
                    (SELECT id FROM menu_master WHERE menu_code = 'ACCOUNT_TRANSACTION' LIMIT 1),
                    '📝', '/account/credit-notes', 7
                WHERE NOT EXISTS (SELECT 1 FROM menu_master WHERE menu_code = 'CREDIT_NOTE')
            """))
            
            session.execute(text("""
                INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order)
                SELECT 'Debit Note', 'DEBIT_NOTE', 'ACCOUNT', 
                    (SELECT id FROM menu_master WHERE menu_code = 'ACCOUNT_TRANSACTION' LIMIT 1),
                    '📄', '/account/debit-notes', 8
                WHERE NOT EXISTS (SELECT 1 FROM menu_master WHERE menu_code = 'DEBIT_NOTE')
            """))
            
            session.commit()
            print("[OK] Migration 044 completed successfully")
            
        except Exception as e:
            session.rollback()
            print(f"[ERROR] Migration 044 failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
