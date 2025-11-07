DROP TABLE IF EXISTS public.bank_accounts;
CREATE TABLE IF NOT EXISTS public.bank_accounts (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    account_number         VARCHAR(50) NOT NULL,
    account_name           VARCHAR(100) NOT NULL,           -- e.g. "HDFC Savings - Main"
    bank_name              VARCHAR(100) NOT NULL,
    branch_name            VARCHAR(100),
    ifsc_code              VARCHAR(20),
    swift_code             VARCHAR(20),

    -- Currency
    currency_id            INTEGER NOT NULL 
                           REFERENCES public.currencies(id) ON DELETE RESTRICT,

    -- Opening Balance
    opening_balance        NUMERIC(15,4) DEFAULT 0,
    opening_date           DATE,

    -- Linked Ledger Account
    account_id             INTEGER NOT NULL 
                           REFERENCES public.account_masters(id) ON DELETE RESTRICT,

    -- Status
    is_active              BOOLEAN DEFAULT TRUE,
    is_default             BOOLEAN DEFAULT FALSE,           -- One default per currency

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_bank_account_number_tenant 
        UNIQUE (account_number, tenant_id)

    -- CONSTRAINT chk_one_default_per_currency 
    --     CHECK (
    --         NOT is_default 
    --         OR (
    --             is_default AND (
    --                 SELECT COUNT(*) 
    --                 FROM bank_accounts b2 
    --                 WHERE b2.tenant_id = bank_accounts.tenant_id 
    --                   AND b2.currency_id = bank_accounts.currency_id 
    --                   AND b2.is_default = TRUE 
    --                   AND b2.is_deleted = FALSE
    --             ) <= 1
    --         )
    --     )
);

-- Indexes
CREATE INDEX idx_bank_accounts_tenant ON public.bank_accounts(tenant_id);
CREATE INDEX idx_bank_accounts_currency ON public.bank_accounts(currency_id);
CREATE INDEX idx_bank_accounts_active ON public.bank_accounts(is_active) 
    WHERE is_active = TRUE AND is_deleted = FALSE;