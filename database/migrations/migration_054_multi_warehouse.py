"""
Migration 054: Multi-Warehouse Management
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    with db_manager.get_session() as session:
        # Warehouses/Locations
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS warehouses (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) NOT NULL,
                address TEXT,
                contact_person VARCHAR(100),
                phone VARCHAR(20),
                email VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                UNIQUE(code, tenant_id)
            )
        """))
        
        # Stock by Location
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_by_location (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                batch_number VARCHAR(50),
                quantity DECIMAL(15,3) DEFAULT 0,
                reserved_quantity DECIMAL(15,3) DEFAULT 0,
                available_quantity DECIMAL(15,3) DEFAULT 0,
                tenant_id INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id, warehouse_id, batch_number, tenant_id)
            )
        """))
        
        # Stock Transfers
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_transfers (
                id SERIAL PRIMARY KEY,
                transfer_number VARCHAR(50) NOT NULL,
                transfer_date DATE NOT NULL,
                from_warehouse_id INTEGER NOT NULL,
                to_warehouse_id INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'DRAFT',
                notes TEXT,
                voucher_id INTEGER,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                approved_at TIMESTAMP,
                approved_by VARCHAR(100),
                UNIQUE(transfer_number, tenant_id)
            )
        """))
        
        # Stock Transfer Items
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_transfer_items (
                id SERIAL PRIMARY KEY,
                transfer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                batch_number VARCHAR(50),
                quantity DECIMAL(15,3) NOT NULL,
                serial_numbers TEXT,
                tenant_id INTEGER NOT NULL,
                FOREIGN KEY (transfer_id) REFERENCES stock_transfers(id) ON DELETE CASCADE
            )
        """))
        
        # Add warehouse to stock transactions
        session.execute(text("""
            ALTER TABLE stock_transactions
            ADD COLUMN IF NOT EXISTS warehouse_id INTEGER
        """))
        
        # Create default warehouse for existing tenants
        session.execute(text("""
            INSERT INTO warehouses (name, code, tenant_id, created_by)
            SELECT 'Main Warehouse', 'WH001', id, 'system' FROM tenants
            WHERE NOT EXISTS (SELECT 1 FROM warehouses WHERE code = 'WH001')
        """))
        
        session.commit()
        print("✓ Multi-warehouse tables created")

def downgrade():
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS stock_transfer_items CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS stock_transfers CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS stock_by_location CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS warehouses CASCADE"))
        session.commit()

if __name__ == "__main__":
    upgrade()
