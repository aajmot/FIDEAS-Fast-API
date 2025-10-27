-- Migration: Add code column to financial_years table
-- Date: 2025-10-27

DO $$
BEGIN
    -- Check if code column already exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'financial_years' AND column_name = 'code'
    ) THEN
        -- Add code column
        ALTER TABLE financial_years ADD COLUMN code VARCHAR(20) DEFAULT NULL;
        
        -- Update existing records to set code based on name
        -- We'll use the name as the code initially, but truncated to 20 chars
        UPDATE financial_years 
        SET code = SUBSTRING(name, 1, 20);
        
        -- Now make the column not nullable
        ALTER TABLE financial_years ALTER COLUMN code SET NOT NULL;
        
        -- Add unique constraint
        ALTER TABLE financial_years 
        ADD CONSTRAINT uq_financial_year_tenant_code 
        UNIQUE (tenant_id, code);
    END IF;


        -- Check if code column already exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'financial_years' AND column_name = 'is_current'
    ) THEN
        -- Add is_current column
        ALTER TABLE financial_years ADD COLUMN is_current BOOLEAN DEFAULT FALSE;
    END IF;




END $$;