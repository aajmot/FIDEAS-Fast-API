DROP TABLE IF EXISTS public.payment_terms;

CREATE TABLE IF NOT EXISTS public.payment_terms (
    id                  SERIAL PRIMARY KEY,

    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) 
                        ON DELETE CASCADE,

    code                VARCHAR(20) NOT NULL,
    name                VARCHAR(100) NOT NULL,
    days                INTEGER NOT NULL 
                        CHECK (days >= 0),

    description         TEXT,
    is_default          BOOLEAN DEFAULT FALSE,
    is_active           BOOLEAN DEFAULT TRUE,
    is_deleted          BOOLEAN DEFAULT FALSE,

    -- Audit
    created_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',

    -- Constraints
    CONSTRAINT uq_payment_term_code_tenant 
        UNIQUE (code, tenant_id),

    CONSTRAINT chk_code_not_empty 
        CHECK (TRIM(code) <> '')
);

-- Indexes
CREATE INDEX idx_payment_terms_tenant ON public.payment_terms(tenant_id);
CREATE INDEX idx_payment_terms_active ON public.payment_terms(is_active) 
    WHERE is_active = TRUE AND is_deleted = FALSE;