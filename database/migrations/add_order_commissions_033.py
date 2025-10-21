#!/usr/bin/env python3
"""
Add Order Commissions Tables Migration
Creates order_commissions and order_commission_items tables
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def create_order_commissions_tables():
    """Create order commissions tables"""
    print("Creating order commissions tables...")
    
    try:
        with db_manager.get_session() as session:
            # Create order_commissions table
            order_commissions_sql = """
            CREATE TABLE IF NOT EXISTS order_commissions (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                order_type TEXT NOT NULL CHECK (order_type IN ('Products', 'Tests')),
                order_id INTEGER NOT NULL,
                order_number TEXT NOT NULL,
                agency_id INTEGER REFERENCES agencies(id),
                agency_name TEXT,
                agency_phone TEXT,
                total_amount DECIMAL(15,2) DEFAULT 0,
                disc_percentage DECIMAL(5,2) DEFAULT 0,
                disc_amount DECIMAL(15,2) DEFAULT 0,
                roundoff DECIMAL(15,2) DEFAULT 0,
                final_amount DECIMAL(15,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            );
            """
            
            # Create order_commission_items table
            order_commission_items_sql = """
            CREATE TABLE IF NOT EXISTS order_commission_items (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                order_commission_id INTEGER NOT NULL REFERENCES order_commissions(id),
                item_type TEXT NOT NULL CHECK (item_type IN ('Products', 'Tests')),
                item_id INTEGER NOT NULL,
                item_name TEXT,
                item_rate DECIMAL(15,2) DEFAULT 0,
                commission_percentage DECIMAL(5,2) DEFAULT 0,
                commission_value DECIMAL(15,2) DEFAULT 0,
                gst_percentage DECIMAL(5,2) DEFAULT 0,
                gst_amount DECIMAL(15,2) DEFAULT 0,
                cess_percentage DECIMAL(5,2) DEFAULT 0,
                cess_amount DECIMAL(15,2) DEFAULT 0,
                total_amount DECIMAL(15,2) DEFAULT 0,
                discount_percentage DECIMAL(5,2) DEFAULT 0,
                discount_amount DECIMAL(15,2) DEFAULT 0,
                roundoff DECIMAL(15,2) DEFAULT 0,
                final_amount DECIMAL(15,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            );
            """
            
            # Create indexes
            indexes_sql = """
            CREATE INDEX IF NOT EXISTS idx_order_commissions_tenant_id ON order_commissions(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_order_commissions_agency_id ON order_commissions(agency_id);
            CREATE INDEX IF NOT EXISTS idx_order_commissions_order_type ON order_commissions(order_type);
            CREATE INDEX IF NOT EXISTS idx_order_commissions_order_id ON order_commissions(order_id);
            CREATE INDEX IF NOT EXISTS idx_order_commission_items_tenant_id ON order_commission_items(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_order_commission_items_order_commission_id ON order_commission_items(order_commission_id);
            CREATE INDEX IF NOT EXISTS idx_order_commission_items_item_type ON order_commission_items(item_type);
            CREATE INDEX IF NOT EXISTS idx_order_commission_items_item_id ON order_commission_items(item_id);
            """
            
            # Execute SQL statements
            statements = [order_commissions_sql, order_commission_items_sql, indexes_sql]
            for sql in statements:
                for stmt in [s.strip() for s in sql.split(';') if s.strip()]:
                    session.execute(text(stmt))
            
            session.commit()
            print("[OK] Order commissions tables created successfully")
            
    except Exception as e:
        print(f"[ERROR] Error creating order commissions tables: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running order commissions migration...")
    create_order_commissions_tables()
    print("Order commissions migration completed!")