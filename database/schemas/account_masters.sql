DROP TABLE IF EXISTS public.account_masters;

CREATE TABLE IF NOT EXISTS public.account_masters (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    parent_id              INTEGER 
                           REFERENCES public.account_masters(id) ON DELETE SET NULL,

    account_group_id       INTEGER NOT NULL 
                           REFERENCES public.account_groups(id) ON DELETE RESTRICT,

    -- Core
    code                   VARCHAR(50) NOT NULL,
    name                   VARCHAR(200) NOT NULL,
    description            TEXT,

    -- Account Type (Critical for GL)
    account_type           VARCHAR(20) NOT NULL 
                           CHECK (account_type IN (
                               'ASSET', 'LIABILITY', 'EQUITY', 
                               'REVENUE', 'EXPENSE'
                           )),

    -- Balance Behavior
    normal_balance         CHAR(1) NOT NULL DEFAULT 'D' 
                           CHECK (normal_balance IN ('D', 'C')),  -- Debit or Credit

    -- System Account (Protected)
    is_system_account      BOOLEAN DEFAULT FALSE,
    system_code            VARCHAR(50),  -- e.g. 'INVENTORY', 'GST_OUTPUT'

    -- Hierarchy
    level                  INTEGER NOT NULL DEFAULT 1 
                           CHECK (level >= 1),
    path                   TEXT,  -- For fast tree queries (PostgreSQL ltree)

    -- Balances
    opening_balance        NUMERIC(15,4) DEFAULT 0,
    current_balance        NUMERIC(15,4) DEFAULT 0,
    is_reconciled          BOOLEAN DEFAULT FALSE,  -- For bank accounts

    -- Status
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',

    -- Constraints
    CONSTRAINT uq_account_code_tenant 
        UNIQUE (code, tenant_id),

    -- CONSTRAINT uq_system_code_tenant 
    --     UNIQUE (system_code, tenant_id) 
    --     WHERE (is_system_account = TRUE),

    CONSTRAINT chk_parent_not_self 
        CHECK (parent_id IS NULL OR parent_id != id)

    -- CONSTRAINT chk_system_account_immutable
    --     CHECK (
    --         NOT is_system_account 
    --         OR (is_system_account AND system_code IS NOT NULL)
    --     )
);

-- Indexes
CREATE INDEX idx_account_masters_tenant ON public.account_masters(tenant_id);
CREATE INDEX idx_account_masters_parent ON public.account_masters(parent_id);
CREATE INDEX idx_account_masters_group ON public.account_masters(account_group_id);
CREATE INDEX idx_account_masters_type ON public.account_masters(account_type);
--CREATE INDEX idx_account_masters_path ON public.account_masters USING GIST (path);
CREATE INDEX idx_account_masters_system ON public.account_masters(system_code) 
    WHERE is_system_account = TRUE;
CREATE INDEX idx_account_masters_active ON public.account_masters(is_active, is_deleted);