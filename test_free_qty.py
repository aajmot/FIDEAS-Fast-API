#!/usr/bin/env python3
"""
Test script to verify free_quantity is being saved correctly in stock transactions
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:admin@localhost:5432/fideas_erp')

print("Testing free_quantity implementation...")
engine = create_engine(database_url)

try:
    with engine.connect() as conn:
        # Check recent purchase invoice items
        print("\n=== Recent Purchase Invoice Items ===")
        result = conn.execute(text("""
            SELECT id, invoice_id, product_id, quantity, free_quantity, 
                   (quantity + COALESCE(free_quantity, 0)) as total_qty
            FROM purchase_invoice_items 
            ORDER BY created_at DESC 
            LIMIT 5
        """))
        for row in result:
            print(f"  ID: {row[0]}, Invoice: {row[1]}, Product: {row[2]}")
            print(f"    Quantity: {row[3]}, Free: {row[4]}, Total: {row[5]}")
        
        # Check recent sales invoice items
        print("\n=== Recent Sales Invoice Items ===")
        result = conn.execute(text("""
            SELECT id, invoice_id, product_id, quantity, free_quantity,
                   (quantity + COALESCE(free_quantity, 0)) as total_qty
            FROM sales_invoice_items 
            ORDER BY created_at DESC 
            LIMIT 5
        """))
        for row in result:
            print(f"  ID: {row[0]}, Invoice: {row[1]}, Product: {row[2]}")
            print(f"    Quantity: {row[3]}, Free: {row[4]}, Total: {row[5]}")
        
        # Check recent stock transactions
        print("\n=== Recent Stock Transactions ===")
        result = conn.execute(text("""
            SELECT id, product_id, transaction_type, transaction_source, 
                   quantity, reference_number
            FROM stock_transactions 
            WHERE transaction_source IN ('PURCHASE_INVOICE', 'SALES_INVOICE')
            ORDER BY created_at DESC 
            LIMIT 10
        """))
        for row in result:
            print(f"  ID: {row[0]}, Product: {row[1]}, Type: {row[2]}, Source: {row[3]}")
            print(f"    Quantity: {row[4]}, Ref: {row[5]}")
            
except Exception as e:
    print(f"✗ Test failed: {e}")
    sys.exit(1)

print("\n✓ Query completed successfully!")
print("\nNote: Create a new invoice with free_quantity to see it reflected in stock_transactions")
