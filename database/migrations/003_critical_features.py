#!/usr/bin/env python3
"""
Critical Features Migration
Adds Tax Management, Multi-Currency, and Bank Reconciliation
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add critical accounting features"""
    print("Adding critical accounting features...")
    
    with db_manager.get_session() as session:
        # Create currencies table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS currencies (
                id SERIAL PRIMARY KEY,
                code VARCHAR(3) NOT NULL UNIQUE,
                name VARCHAR(50) NOT NULL,
                symbol VARCHAR(5),
                is_base BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create exchange_rates table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id SERIAL PRIMARY KEY,
                from_currency_id INTEGER NOT NULL REFERENCES currencies(id),
                to_currency_id INTEGER NOT NULL REFERENCES currencies(id),
                rate NUMERIC(15, 6) NOT NULL,
                effective_date DATE NOT NULL,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_exchange_rate UNIQUE (from_currency_id, to_currency_id, effective_date, tenant_id)
            )
        """))
        
        # Create tax_masters table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS tax_masters (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                tax_type VARCHAR(20) NOT NULL,
                rate NUMERIC(5, 2) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_tax_master_name_tenant UNIQUE (name, tenant_id)
            )
        """))
        
        # Create bank_reconciliations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS bank_reconciliations (
                id SERIAL PRIMARY KEY,
                bank_account_id INTEGER NOT NULL REFERENCES account_masters(id),
                statement_date DATE NOT NULL,
                statement_balance NUMERIC(15, 2) NOT NULL,
                book_balance NUMERIC(15, 2) NOT NULL,
                reconciled_balance NUMERIC(15, 2) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'DRAFT',
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            )
        """))
        
        # Create bank_reconciliation_items table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS bank_reconciliation_items (
                id SERIAL PRIMARY KEY,
                reconciliation_id INTEGER NOT NULL REFERENCES bank_reconciliations(id),
                ledger_id INTEGER REFERENCES ledgers(id),
                statement_amount NUMERIC(15, 2) NOT NULL,
                statement_date DATE NOT NULL,
                statement_reference VARCHAR(100),
                is_matched BOOLEAN DEFAULT FALSE,
                match_type VARCHAR(20),
                tenant_id INTEGER NOT NULL REFERENCES tenants(id)
            )
        """))
        
        # Add currency columns to vouchers
        session.execute(text("""
            ALTER TABLE vouchers 
            ADD COLUMN IF NOT EXISTS currency_id INTEGER REFERENCES currencies(id),
            ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(15, 6) DEFAULT 1,
            ADD COLUMN IF NOT EXISTS base_currency_amount NUMERIC(15, 2),
            ADD COLUMN IF NOT EXISTS reversed_voucher_id INTEGER REFERENCES vouchers(id),
            ADD COLUMN IF NOT EXISTS reversal_voucher_id INTEGER REFERENCES vouchers(id),
            ADD COLUMN IF NOT EXISTS is_reversal BOOLEAN DEFAULT FALSE
        """))
        
        # Add tax columns to journal_details
        session.execute(text("""
            ALTER TABLE journal_details 
            ADD COLUMN IF NOT EXISTS tax_id INTEGER REFERENCES tax_masters(id),
            ADD COLUMN IF NOT EXISTS taxable_amount NUMERIC(15, 2) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS tax_amount NUMERIC(15, 2) DEFAULT 0
        """))
        
        session.commit()
        print("[OK] Critical features tables created")
        
        # Insert default currencies
        session.execute(text("""
            INSERT INTO currencies (code, name, symbol, is_base, is_active)
            VALUES 
                ('INR', 'Indian Rupee', '₹', TRUE, TRUE),
                ('USD', 'US Dollar', '$', FALSE, TRUE),
                ('EUR', 'Euro', '€', FALSE, TRUE),
                ('GBP', 'British Pound', '£', FALSE, TRUE),
                ('AED', 'UAE Dirham', 'د.إ', FALSE, TRUE)
            ON CONFLICT (code) DO NOTHING
        """))
        
        session.commit()
        print("[OK] Default currencies inserted")

if __name__ == "__main__":
    print("Running critical features migration...")
    upgrade()
    print("Migration completed!")
