"""
Migration 052: Invoice Management
- Sales Invoice
- Purchase Invoice
- Proforma Invoice
- Invoice Items
- Payment Terms
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    with db_manager.get_session() as session:
        # Payment Terms Master
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS payment_terms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) NOT NULL,
                days INTEGER NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                UNIQUE(code, tenant_id)
            )
        """))
        
        # Sales Invoice
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS sales_invoices (
                id SERIAL PRIMARY KEY,
                invoice_number VARCHAR(50) NOT NULL,
                invoice_date DATE NOT NULL,
                customer_id INTEGER NOT NULL,
                sales_order_id INTEGER,
                payment_term_id INTEGER,
                due_date DATE,
                subtotal DECIMAL(15,2) DEFAULT 0,
                discount_percent DECIMAL(5,2) DEFAULT 0,
                discount_amount DECIMAL(15,2) DEFAULT 0,
                tax_amount DECIMAL(15,2) DEFAULT 0,
                total_amount DECIMAL(15,2) NOT NULL,
                paid_amount DECIMAL(15,2) DEFAULT 0,
                balance_amount DECIMAL(15,2) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'DRAFT',
                invoice_type VARCHAR(20) DEFAULT 'TAX_INVOICE',
                notes TEXT,
                terms_conditions TEXT,
                is_einvoice BOOLEAN DEFAULT FALSE,
                einvoice_irn VARCHAR(100),
                einvoice_ack_no VARCHAR(50),
                einvoice_ack_date TIMESTAMP,
                eway_bill_no VARCHAR(50),
                eway_bill_date TIMESTAMP,
                voucher_id INTEGER,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP,
                updated_by VARCHAR(100),
                UNIQUE(invoice_number, tenant_id)
            )
        """))
        
        # Sales Invoice Items
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS sales_invoice_items (
                id SERIAL PRIMARY KEY,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                description TEXT,
                quantity DECIMAL(15,3) NOT NULL,
                unit_price DECIMAL(15,2) NOT NULL,
                discount_percent DECIMAL(5,2) DEFAULT 0,
                discount_amount DECIMAL(15,2) DEFAULT 0,
                taxable_amount DECIMAL(15,2) NOT NULL,
                cgst_rate DECIMAL(5,2) DEFAULT 0,
                cgst_amount DECIMAL(15,2) DEFAULT 0,
                sgst_rate DECIMAL(5,2) DEFAULT 0,
                sgst_amount DECIMAL(15,2) DEFAULT 0,
                igst_rate DECIMAL(5,2) DEFAULT 0,
                igst_amount DECIMAL(15,2) DEFAULT 0,
                total_amount DECIMAL(15,2) NOT NULL,
                hsn_code VARCHAR(20),
                batch_number VARCHAR(50),
                serial_numbers TEXT,
                tenant_id INTEGER NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES sales_invoices(id) ON DELETE CASCADE
            )
        """))
        
        # Purchase Invoice
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS purchase_invoices (
                id SERIAL PRIMARY KEY,
                invoice_number VARCHAR(50) NOT NULL,
                invoice_date DATE NOT NULL,
                supplier_id INTEGER NOT NULL,
                purchase_order_id INTEGER,
                payment_term_id INTEGER,
                due_date DATE,
                subtotal DECIMAL(15,2) DEFAULT 0,
                discount_percent DECIMAL(5,2) DEFAULT 0,
                discount_amount DECIMAL(15,2) DEFAULT 0,
                tax_amount DECIMAL(15,2) DEFAULT 0,
                total_amount DECIMAL(15,2) NOT NULL,
                paid_amount DECIMAL(15,2) DEFAULT 0,
                balance_amount DECIMAL(15,2) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'DRAFT',
                notes TEXT,
                voucher_id INTEGER,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP,
                updated_by VARCHAR(100),
                UNIQUE(invoice_number, tenant_id)
            )
        """))
        
        # Purchase Invoice Items
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS purchase_invoice_items (
                id SERIAL PRIMARY KEY,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                description TEXT,
                quantity DECIMAL(15,3) NOT NULL,
                unit_price DECIMAL(15,2) NOT NULL,
                discount_percent DECIMAL(5,2) DEFAULT 0,
                discount_amount DECIMAL(15,2) DEFAULT 0,
                taxable_amount DECIMAL(15,2) NOT NULL,
                cgst_rate DECIMAL(5,2) DEFAULT 0,
                cgst_amount DECIMAL(15,2) DEFAULT 0,
                sgst_rate DECIMAL(5,2) DEFAULT 0,
                sgst_amount DECIMAL(15,2) DEFAULT 0,
                igst_rate DECIMAL(5,2) DEFAULT 0,
                igst_amount DECIMAL(15,2) DEFAULT 0,
                total_amount DECIMAL(15,2) NOT NULL,
                hsn_code VARCHAR(20),
                batch_number VARCHAR(50),
                serial_numbers TEXT,
                tenant_id INTEGER NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES purchase_invoices(id) ON DELETE CASCADE
            )
        """))
        
        # Update customers table for credit management
        session.execute(text("""
            ALTER TABLE customers 
            ADD COLUMN IF NOT EXISTS credit_limit DECIMAL(15,2) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS payment_term_id INTEGER,
            ADD COLUMN IF NOT EXISTS credit_hold BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS outstanding_balance DECIMAL(15,2) DEFAULT 0
        """))
        
        # Insert default payment terms
        session.execute(text("""
            INSERT INTO payment_terms (name, code, days, tenant_id, created_by)
            SELECT 'Immediate', 'IMM', 0, id, 'system' FROM tenants
            WHERE NOT EXISTS (SELECT 1 FROM payment_terms WHERE code = 'IMM')
        """))
        
        session.execute(text("""
            INSERT INTO payment_terms (name, code, days, tenant_id, created_by)
            SELECT 'Net 30', 'NET30', 30, id, 'system' FROM tenants
            WHERE NOT EXISTS (SELECT 1 FROM payment_terms WHERE code = 'NET30')
        """))
        
        session.execute(text("""
            INSERT INTO payment_terms (name, code, days, tenant_id, created_by)
            SELECT 'Net 60', 'NET60', 60, id, 'system' FROM tenants
            WHERE NOT EXISTS (SELECT 1 FROM payment_terms WHERE code = 'NET60')
        """))
        
        session.commit()
        print("✓ Invoice management tables created")

def downgrade():
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS purchase_invoice_items CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS purchase_invoices CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS sales_invoice_items CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS sales_invoices CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS payment_terms CASCADE"))
        session.commit()

if __name__ == "__main__":
    upgrade()
