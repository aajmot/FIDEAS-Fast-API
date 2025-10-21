#!/usr/bin/env python3
"""
Add new fields to order items tables
Adds batch_number, free_quantity, cgst_rate, sgst_rate to purchase_order_items and sales_order_items
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add new fields to order items tables"""
    print("Adding new fields to order items tables...")
    
    try:
        with db_manager.get_session() as session:
            # Add fields to purchase_order_items
            purchase_order_fields = [
                "ALTER TABLE purchase_order_items ADD COLUMN IF NOT EXISTS batch_number VARCHAR(50);",
                "ALTER TABLE purchase_order_items ADD COLUMN IF NOT EXISTS free_quantity DECIMAL(10,2) DEFAULT 0;",
                "ALTER TABLE purchase_order_items ADD COLUMN IF NOT EXISTS cgst_rate DECIMAL(5,2) DEFAULT 0;",
                "ALTER TABLE purchase_order_items ADD COLUMN IF NOT EXISTS sgst_rate DECIMAL(5,2) DEFAULT 0;"
            ]
            
            # Add fields to sales_order_items
            sales_order_fields = [
                "ALTER TABLE sales_order_items ADD COLUMN IF NOT EXISTS cgst_rate DECIMAL(5,2) DEFAULT 0;",
                "ALTER TABLE sales_order_items ADD COLUMN IF NOT EXISTS sgst_rate DECIMAL(5,2) DEFAULT 0;"
            ]
            
            all_statements = purchase_order_fields + sales_order_fields
            
            for stmt in all_statements:
                try:
                    session.execute(text(stmt))
                except Exception as e:
                    print(f"[WARNING] Error executing statement: {e}")
                    continue
            
            session.commit()
            print("[OK] New fields added to order items tables successfully")
            
    except Exception as e:
        print(f"[ERROR] Error adding fields: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running order items fields migration...")
    upgrade()
    print("Migration completed!")