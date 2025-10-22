-- Migration script to align FastAPI models with database schema
-- Run this script to ensure model compatibility

BEGIN;

-- Add missing columns to users table if they do not exist
DO $$
BEGIN
    -- Add is_deleted column if it does not exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'is_deleted') THEN
        ALTER TABLE users ADD COLUMN is_deleted boolean DEFAULT false;
    END IF;
    
    -- Add updated_at column if it does not exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'updated_at') THEN
        ALTER TABLE users ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Add missing columns to accounts table if they do not exist
DO $$
BEGIN
    -- Add tenant_id column if it does not exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'accounts' AND column_name = 'tenant_id') THEN
        ALTER TABLE accounts ADD COLUMN tenant_id integer;
        -- Add foreign key constraint
        ALTER TABLE accounts ADD CONSTRAINT accounts_tenant_id_fkey 
            FOREIGN KEY (tenant_id) REFERENCES tenants (id);
    END IF;
END $$;

-- Add missing columns to transactions table if they do not exist  
DO $$
BEGIN
    -- Add tenant_id column if it does not exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'transactions' AND column_name = 'tenant_id') THEN
        ALTER TABLE transactions ADD COLUMN tenant_id integer;
        -- Add foreign key constraint
        ALTER TABLE transactions ADD CONSTRAINT transactions_tenant_id_fkey 
            FOREIGN KEY (tenant_id) REFERENCES tenants (id);
    END IF;
END $$;

-- Ensure all tables have proper audit columns
DO $$
DECLARE
    table_record RECORD;
    audit_tables TEXT[] := ARRAY['categories', 'products', 'customers', 'suppliers', 'units', 'patients', 'doctors', 'appointments', 'test_panels'];
BEGIN
    FOR table_record IN 
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = ANY(audit_tables)
    LOOP
        -- Add is_deleted if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name = table_record.table_name AND column_name = 'is_deleted') THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN is_deleted boolean DEFAULT false', table_record.table_name);
        END IF;
        
        -- Add updated_at if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name = table_record.table_name AND column_name = 'updated_at') THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP', table_record.table_name);
        END IF;
        
        -- Add updated_by if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name = table_record.table_name AND column_name = 'updated_by') THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN updated_by character varying(100)', table_record.table_name);
        END IF;
    END LOOP;
END $$;

COMMIT;