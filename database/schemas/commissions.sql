DROP TABLE IF EXISTS public.commissions;
CREATE TABLE IF NOT EXISTS public.commissions (
    id                  SERIAL PRIMARY KEY,
    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) ON DELETE CASCADE,

    agent_id            INTEGER NOT NULL 
                        REFERENCES public.agencies(id) ON DELETE RESTRICT,
    
    voucher_type_id     INTEGER NOT NULL 
                        REFERENCES public.voucher_types(id) ON DELETE RESTRICT,

    basis               VARCHAR(20) 
                        CHECK (basis IN ('percentage', 'fixed')) 
                        DEFAULT 'percentage',
    
    value               NUMERIC(12,4) NOT NULL,         -- 5.00 or 500.00
    tax_id              INTEGER 
                        REFERENCES public.taxes(id) ON DELETE SET NULL,

    is_active           BOOLEAN DEFAULT TRUE,

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_deleted          BOOLEAN DEFAULT FALSE,

    CONSTRAINT uq_commission_agent_vtype UNIQUE (agent_id, voucher_type_id, tenant_id)
);