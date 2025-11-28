-- Migration: Make account_id nullable in payment_details table
-- Date: 2024-11-28
-- Description: Allow account_id to be null in payment_details as it will be auto-determined by the service

-- Make account_id column nullable
ALTER TABLE payment_details ALTER COLUMN account_id DROP NOT NULL;

-- Add comment to document the change
COMMENT ON COLUMN payment_details.account_id IS 'Account ID for payment - auto-determined if not provided based on payment mode';