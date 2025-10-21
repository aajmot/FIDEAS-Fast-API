"""
Migration 055: Fixed Asset Management
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    with db_manager.get_session() as session:
        # Asset Categories
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS asset_categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) NOT NULL,
                depreciation_method VARCHAR(20) DEFAULT 'SLM',
                depreciation_rate DECIMAL(5,2) DEFAULT 0,
                useful_life_years INTEGER DEFAULT 5,
                account_id INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, tenant_id)
            )
        """))
        
        # Fixed Assets
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS fixed_assets (
                id SERIAL PRIMARY KEY,
                asset_number VARCHAR(50) NOT NULL,
                name VARCHAR(200) NOT NULL,
                category_id INTEGER NOT NULL,
                purchase_date DATE NOT NULL,
                purchase_cost DECIMAL(15,2) NOT NULL,
                salvage_value DECIMAL(15,2) DEFAULT 0,
                useful_life_years INTEGER NOT NULL,
                depreciation_method VARCHAR(20) DEFAULT 'SLM',
                depreciation_rate DECIMAL(5,2),
                accumulated_depreciation DECIMAL(15,2) DEFAULT 0,
                book_value DECIMAL(15,2),
                status VARCHAR(20) DEFAULT 'ACTIVE',
                location VARCHAR(200),
                serial_number VARCHAR(100),
                supplier_id INTEGER,
                purchase_invoice_id INTEGER,
                disposal_date DATE,
                disposal_value DECIMAL(15,2),
                disposal_notes TEXT,
                notes TEXT,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                UNIQUE(asset_number, tenant_id)
            )
        """))
        
        # Depreciation Schedule
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS depreciation_schedule (
                id SERIAL PRIMARY KEY,
                asset_id INTEGER NOT NULL,
                period_date DATE NOT NULL,
                opening_value DECIMAL(15,2) NOT NULL,
                depreciation_amount DECIMAL(15,2) NOT NULL,
                closing_value DECIMAL(15,2) NOT NULL,
                is_posted BOOLEAN DEFAULT FALSE,
                voucher_id INTEGER,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES fixed_assets(id) ON DELETE CASCADE
            )
        """))
        
        session.commit()
        print("✓ Fixed asset tables created")

def downgrade():
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS depreciation_schedule CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS fixed_assets CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS asset_categories CASCADE"))
        session.commit()

if __name__ == "__main__":
    upgrade()
