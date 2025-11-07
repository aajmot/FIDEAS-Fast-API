DROP TABLE IF EXISTS public.voucher_types CASCADE;
CREATE TABLE IF NOT EXISTS public.voucher_types (
    id                  SERIAL PRIMARY KEY,
    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) ON DELETE CASCADE,
    
    name                VARCHAR(50) NOT NULL,
    code                VARCHAR(50) NOT NULL,
    prefix              VARCHAR(50),
    
    allow_multi_currency BOOLEAN DEFAULT TRUE,
    allow_tax           BOOLEAN DEFAULT TRUE,
    allow_commission    BOOLEAN DEFAULT TRUE,
    
    is_active           BOOLEAN DEFAULT TRUE,
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_deleted          BOOLEAN DEFAULT FALSE,

    CONSTRAINT uq_voucher_type_code_tenant UNIQUE (code, tenant_id)

);