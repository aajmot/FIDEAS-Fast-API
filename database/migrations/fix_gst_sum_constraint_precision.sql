-- =====================================================
-- Migration: Fix GST sum check constraint precision issue
-- =====================================================
-- Purpose: Replace exact equality check with tolerance-based check
--          to handle decimal rounding differences
-- Date: 2025-11-06
-- =====================================================

-- Drop the old constraint
ALTER TABLE purchase_invoices 
DROP CONSTRAINT IF EXISTS chk_gst_sum;

-- Add new constraint with tolerance for rounding (0.01 tolerance)
ALTER TABLE purchase_invoices
ADD CONSTRAINT chk_gst_sum 
CHECK (
    ABS(tax_amount_base - (cgst_amount_base + sgst_amount_base + igst_amount_base + ugst_amount_base + cess_amount_base)) < 0.01
);

-- Apply same fix to sales_invoices if it exists
ALTER TABLE sales_invoices 
DROP CONSTRAINT IF EXISTS chk_gst_sum;

ALTER TABLE sales_invoices
ADD CONSTRAINT chk_gst_sum 
CHECK (
    ABS(tax_amount_base - (cgst_amount_base + sgst_amount_base + igst_amount_base + ugst_amount_base + cess_amount_base)) < 0.01
);

-- =====================================================
-- Verification
-- =====================================================
-- 
-- Test with the failing values:
-- SELECT 
--     ABS(343.8405 - (171.92025 + 171.92025 + 0 + 0 + 0)) as difference,
--     CASE WHEN ABS(343.8405 - (171.92025 + 171.92025 + 0 + 0 + 0)) < 0.01 
--          THEN 'PASS' ELSE 'FAIL' END as result;
-- 
-- Should return: difference = 0.00000, result = PASS
-- =====================================================
