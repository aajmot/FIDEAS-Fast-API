#!/usr/bin/env python3
"""
Script to run the free_quantity migration
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:admin@localhost:5432/fideas_erp')

print(f"Connecting to database...")
engine = create_engine(database_url)

migration_sql = """
-- Add free_quantity to purchase_invoice_items
ALTER TABLE purchase_invoice_items 
ADD COLUMN IF NOT EXISTS free_quantity NUMERIC(15,4) DEFAULT 0;

COMMENT ON COLUMN purchase_invoice_items.free_quantity IS 'Complimentary/bonus quantity provided free of cost';

-- Add free_quantity to sales_invoice_items  
ALTER TABLE sales_invoice_items 
ADD COLUMN IF NOT EXISTS free_quantity NUMERIC(15,4) DEFAULT 0;

COMMENT ON COLUMN sales_invoice_items.free_quantity IS 'Complimentary/bonus quantity provided free of cost';

-- Update existing records to have 0 free_quantity
UPDATE purchase_invoice_items SET free_quantity = 0 WHERE free_quantity IS NULL;
UPDATE sales_invoice_items SET free_quantity = 0 WHERE free_quantity IS NULL;
"""

try:
    with engine.connect() as conn:
        print("Running migration...")
        conn.execute(text(migration_sql))
        conn.commit()
        print("✓ Migration completed successfully!")
        
        # Verify the columns were added
        print("\nVerifying purchase_invoice_items...")
        result = conn.execute(text("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'purchase_invoice_items' 
            AND column_name = 'free_quantity'
        """))
        for row in result:
            print(f"  Column: {row[0]}, Type: {row[1]}, Default: {row[2]}")
        
        print("\nVerifying sales_invoice_items...")
        result = conn.execute(text("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'sales_invoice_items' 
            AND column_name = 'free_quantity'
        """))
        for row in result:
            print(f"  Column: {row[0]}, Type: {row[1]}, Default: {row[2]}")
            
except Exception as e:
    print(f"✗ Migration failed: {e}")
    sys.exit(1)
