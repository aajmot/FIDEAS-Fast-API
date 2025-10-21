"""
Migration 053: Barcode & Serial Number Tracking
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    with db_manager.get_session() as session:
        # Add barcode to products
        session.execute(text("""
            ALTER TABLE products 
            ADD COLUMN IF NOT EXISTS barcode VARCHAR(100),
            ADD COLUMN IF NOT EXISTS is_serialized BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS warranty_months INTEGER DEFAULT 0
        """))
        
        # Serial Numbers
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS serial_numbers (
                id SERIAL PRIMARY KEY,
                serial_number VARCHAR(100) NOT NULL,
                product_id INTEGER NOT NULL,
                batch_number VARCHAR(50),
                status VARCHAR(20) DEFAULT 'IN_STOCK',
                purchase_invoice_id INTEGER,
                sales_invoice_id INTEGER,
                warranty_expiry_date DATE,
                location_id INTEGER,
                notes TEXT,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(serial_number, tenant_id)
            )
        """))
        
        # Batch tracking with expiry
        session.execute(text("""
            ALTER TABLE stock_transactions
            ADD COLUMN IF NOT EXISTS expiry_date DATE,
            ADD COLUMN IF NOT EXISTS manufacturing_date DATE
        """))
        
        session.commit()
        print("✓ Barcode and serial number tables created")

def downgrade():
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS serial_numbers CASCADE"))
        session.commit()

if __name__ == "__main__":
    upgrade()
