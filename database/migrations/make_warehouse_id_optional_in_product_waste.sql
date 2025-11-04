-- Migration: Make warehouse_id optional in product_waste table
-- Date: 2025-11-03
-- Description: Change warehouse_id from NOT NULL to nullable and update unique constraint

-- Step 1: Drop existing unique constraint that includes warehouse_id
ALTER TABLE public.product_waste 
DROP CONSTRAINT IF EXISTS uq_waste_number_tenant_warehouse;

-- Step 2: Make warehouse_id nullable
ALTER TABLE public.product_waste 
ALTER COLUMN warehouse_id DROP NOT NULL;

-- Step 3: Add new unique constraint without warehouse_id
-- This ensures waste_number is unique per tenant regardless of warehouse
ALTER TABLE public.product_waste 
ADD CONSTRAINT uq_waste_number_tenant UNIQUE (waste_number, tenant_id);

-- Note: The foreign key constraint and index on warehouse_id remain intact
-- This allows optional warehouse tracking while maintaining referential integrity when provided
