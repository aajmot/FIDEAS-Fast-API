-- Migration: Add free_quantity to invoice items tables
-- Date: 2025-11-24
-- Description: Add free_quantity field to both purchase and sales invoice items to track complimentary/bonus items

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
