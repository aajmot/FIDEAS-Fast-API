DROP TABLE IF EXISTS public.taxes;

CREATE TABLE IF NOT EXISTS public.taxes (
    id                  SERIAL PRIMARY KEY,
    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) ON DELETE CASCADE,

    code                VARCHAR(20) NOT NULL,           -- e.g. GST18, VAT12
    name                VARCHAR(100) NOT NULL,          -- GST 18%
    rate                NUMERIC(6,4) NOT NULL,          -- 18.0000
    is_compound         BOOLEAN DEFAULT FALSE,
    is_active           BOOLEAN DEFAULT TRUE,

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_deleted          BOOLEAN DEFAULT FALSE,

    CONSTRAINT uq_tax_code_tenant UNIQUE (code, tenant_id)
);