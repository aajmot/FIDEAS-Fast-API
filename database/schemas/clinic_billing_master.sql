DROP TABLE IF EXISTS public.clinic_billing_master;

CREATE TABLE IF NOT EXISTS public.clinic_billing_master (
    id                  SERIAL PRIMARY KEY,
    
    tenant_id           INTEGER NOT NULL
                        REFERENCES public.tenants(id) ON DELETE CASCADE,
    
    description         TEXT NOT NULL,
    note                TEXT,
    amount              NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    
    hsn_code            VARCHAR(20),
    gst_percentage      NUMERIC(5,2) NOT NULL DEFAULT 0.00 
                        CHECK (gst_percentage >= 0 AND gst_percentage <= 100),
    
    -- Audit
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_active           BOOLEAN DEFAULT TRUE,
    is_deleted          BOOLEAN DEFAULT FALSE
);

-- Indexes
CREATE INDEX idx_clinic_billing_master_tenant ON public.clinic_billing_master(tenant_id);
CREATE INDEX idx_clinic_billing_master_hsn_code ON public.clinic_billing_master(hsn_code);
CREATE INDEX idx_clinic_billing_master_active_deleted ON public.clinic_billing_master(is_active, is_deleted);
