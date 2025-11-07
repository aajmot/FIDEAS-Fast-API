DROP TABLE IF EXISTS public.account_configurations;
CREATE TABLE IF NOT EXISTS public.account_configurations (
    id                  SERIAL PRIMARY KEY,

    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) ON DELETE CASCADE,

    config_key_id       INTEGER NOT NULL 
                        REFERENCES public.account_configuration_keys(id) ON DELETE RESTRICT,

    account_id          INTEGER NOT NULL 
                        REFERENCES public.account_masters(id) ON DELETE RESTRICT,

    -- Optional: Module-specific (e.g. PURCHASE, SALES)
    module              VARCHAR(30),

    -- Audit
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_deleted          BOOLEAN DEFAULT FALSE

    -- Constraints
    -- CONSTRAINT uq_tenant_config 
    --     UNIQUE (tenant_id, config_key_id, COALESCE(module, 'DEFAULT')),

    -- CONSTRAINT chk_account_not_default 
    --     CHECK (account_id != (SELECT default_account_id FROM account_configuration_keys WHERE id = config_key_id))
);

-- Indexes
CREATE INDEX idx_account_config_tenant ON public.account_configurations(tenant_id);
CREATE INDEX idx_account_config_key ON public.account_configurations(config_key_id);