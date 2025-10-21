"""
Migration 058: GST Compliance & E-Invoicing
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    with db_manager.get_session() as session:
        # GST Configuration
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS gst_configuration (
                id SERIAL PRIMARY KEY,
                gstin VARCHAR(15) NOT NULL,
                legal_name VARCHAR(200) NOT NULL,
                trade_name VARCHAR(200),
                state_code VARCHAR(2) NOT NULL,
                is_composition BOOLEAN DEFAULT FALSE,
                einvoice_enabled BOOLEAN DEFAULT FALSE,
                einvoice_username VARCHAR(100),
                einvoice_password VARCHAR(255),
                api_endpoint VARCHAR(255),
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tenant_id)
            )
        """))
        
        # GSTR-1 Data
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS gstr1_data (
                id SERIAL PRIMARY KEY,
                return_period VARCHAR(7) NOT NULL,
                invoice_id INTEGER NOT NULL,
                invoice_type VARCHAR(20),
                gstin VARCHAR(15),
                taxable_value DECIMAL(15,2),
                cgst_amount DECIMAL(15,2),
                sgst_amount DECIMAL(15,2),
                igst_amount DECIMAL(15,2),
                cess_amount DECIMAL(15,2),
                is_filed BOOLEAN DEFAULT FALSE,
                filed_date TIMESTAMP,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # E-Way Bills
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS eway_bills (
                id SERIAL PRIMARY KEY,
                eway_bill_no VARCHAR(50) NOT NULL,
                invoice_id INTEGER NOT NULL,
                invoice_type VARCHAR(20),
                generated_date TIMESTAMP NOT NULL,
                valid_upto TIMESTAMP,
                vehicle_number VARCHAR(20),
                transporter_id VARCHAR(15),
                distance INTEGER,
                status VARCHAR(20) DEFAULT 'ACTIVE',
                tenant_id INTEGER NOT NULL,
                UNIQUE(eway_bill_no, tenant_id)
            )
        """))
        
        # TDS Configuration
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS tds_rates (
                id SERIAL PRIMARY KEY,
                section VARCHAR(20) NOT NULL,
                description TEXT,
                rate DECIMAL(5,2) NOT NULL,
                threshold_limit DECIMAL(15,2),
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # TDS Deductions
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS tds_deductions (
                id SERIAL PRIMARY KEY,
                payment_id INTEGER NOT NULL,
                section VARCHAR(20) NOT NULL,
                gross_amount DECIMAL(15,2) NOT NULL,
                tds_rate DECIMAL(5,2) NOT NULL,
                tds_amount DECIMAL(15,2) NOT NULL,
                net_amount DECIMAL(15,2) NOT NULL,
                deduction_date DATE NOT NULL,
                challan_number VARCHAR(50),
                challan_date DATE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        session.commit()
        print("✓ GST compliance tables created")

def downgrade():
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS tds_deductions CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS tds_rates CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS eway_bills CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS gstr1_data CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS gst_configuration CASCADE"))
        session.commit()

if __name__ == "__main__":
    upgrade()
