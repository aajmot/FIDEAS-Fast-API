DROP TABLE IF EXISTS public.account_configuration_keys;
CREATE TABLE IF NOT EXISTS public.account_configuration_keys (
    id                  SERIAL PRIMARY KEY,

    code                VARCHAR(50) NOT NULL,      -- e.g. INVENTORY, GST_OUTPUT
    name                VARCHAR(100) NOT NULL,     -- Human readable
    description         TEXT,
    is_active           BOOLEAN DEFAULT TRUE,

    -- Default account (global fallback)
    default_account_id  INTEGER 
                        REFERENCES public.account_masters(id) ON DELETE SET NULL,

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted          BOOLEAN DEFAULT FALSE,

    CONSTRAINT uq_config_key_code UNIQUE (code)
);

-- Indexes
CREATE INDEX idx_config_keys_active ON public.account_configuration_keys(is_active) 
    WHERE is_active = TRUE AND is_deleted = FALSE;