-- Migration: Add audit columns to warehouses table
-- Date: 2025-01-23

-- Add audit columns if they don't exist
DO $$
BEGIN
    -- Add created_at column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'warehouses' AND column_name = 'created_at') THEN
        ALTER TABLE warehouses ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
    END IF;

    -- Add created_by column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'warehouses' AND column_name = 'created_by') THEN
        ALTER TABLE warehouses ADD COLUMN created_by VARCHAR(100);
    END IF;

    -- Add updated_at column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'warehouses' AND column_name = 'updated_at') THEN
        ALTER TABLE warehouses ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
    END IF;

    -- Add updated_by column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'warehouses' AND column_name = 'updated_by') THEN
        ALTER TABLE warehouses ADD COLUMN updated_by VARCHAR(100);
    END IF;

    -- Add is_deleted column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'warehouses' AND column_name = 'is_deleted') THEN
        ALTER TABLE warehouses ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add is_active column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'warehouses' AND column_name = 'is_active') THEN
        ALTER TABLE warehouses ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- Create trigger for updated_at auto-update
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop trigger if exists and create new one
DROP TRIGGER IF EXISTS update_warehouses_updated_at ON warehouses;
CREATE TRIGGER update_warehouses_updated_at
    BEFORE UPDATE ON warehouses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();