-- Table: public.tenant_settings
DROP TABLE IF EXISTS public.tenant_settings;

CREATE TABLE public.tenant_settings
(
    id                  SERIAL PRIMARY KEY,
    -- Each tenant has exactly one row; using tenant_id as the primary key is more efficient
    tenant_id integer NOT NULL,
    
    -- Feature Flags
    enable_inventory BOOLEAN NOT NULL DEFAULT TRUE,
    enable_gst BOOLEAN NOT NULL DEFAULT TRUE,
    enable_bank_entry BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Configurations
    base_currency TEXT NOT NULL DEFAULT 'INR',

    -- Payment Modes
    payment_modes TEXT[] NOT NULL DEFAULT ARRAY['CASH','UPI'],
    default_payment_mode TEXT NOT NULL DEFAULT 'CASH',
     
    -- Metadata
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT,

    CONSTRAINT tenant_settings_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) ON DELETE CASCADE
);
-- Add index for query performance
CREATE INDEX idx_tenant_settings_tenant_id ON public.tenant_settings(tenant_id);
