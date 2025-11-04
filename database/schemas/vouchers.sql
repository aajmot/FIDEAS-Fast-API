DROP TABLE IF EXISTS public.voucher_lines;
DROP TABLE IF EXISTS public.vouchers;
CREATE TABLE IF NOT EXISTS public.vouchers (
    id                  SERIAL PRIMARY KEY,
    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) ON DELETE CASCADE,

    voucher_number      VARCHAR(50) NOT NULL,
    voucher_type_id     INTEGER NOT NULL 
                        REFERENCES public.voucher_types(id) ON DELETE RESTRICT,
    
    voucher_date        TIMESTAMP NOT NULL,

    -- Currency
    base_currency_id    INTEGER NOT NULL 
                        REFERENCES public.currencies(id) ON DELETE RESTRICT,
    foreign_currency_id INTEGER 
                        REFERENCES public.currencies(id) ON DELETE SET NULL,
    exchange_rate       NUMERIC(15,4) DEFAULT 1,

    -- Base Currency Totals (Always Required)
    base_total_amount   NUMERIC(15,4) NOT NULL DEFAULT 0,
    base_total_debit    NUMERIC(15,4) NOT NULL DEFAULT 0,
    base_total_credit   NUMERIC(15,4) NOT NULL DEFAULT 0,

    -- Foreign Currency Totals (Optional)
    foreign_total_amount NUMERIC(15,4),
    foreign_total_debit  NUMERIC(15,4),
    foreign_total_credit NUMERIC(15,4),

    -- References
    reference_type      VARCHAR(20),
    reference_id        INTEGER,
    reference_number    VARCHAR(50),

    narration           TEXT,
    
    -- Posting & Reversal
    is_posted           BOOLEAN DEFAULT TRUE,
    reversed_voucher_id INTEGER 
                        REFERENCES public.vouchers(id) ON DELETE SET NULL,
    reversal_voucher_id INTEGER 
                        REFERENCES public.vouchers(id) ON DELETE SET NULL,
    is_reversal         BOOLEAN DEFAULT FALSE,

    -- Approval
    approval_status     VARCHAR(20),
    approval_request_id INTEGER,

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          TEXT DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          TEXT DEFAULT 'system',
    is_deleted          BOOLEAN DEFAULT FALSE,

    CONSTRAINT uq_voucher_number_tenant UNIQUE (voucher_number, tenant_id),
    CONSTRAINT chk_currency_logic 
        CHECK (
            (foreign_currency_id IS NULL AND exchange_rate = 1 AND 
             foreign_total_amount IS NULL AND foreign_total_debit IS NULL AND foreign_total_credit IS NULL)
            OR
            (foreign_currency_id IS NOT NULL AND exchange_rate > 0)
        )
);

CREATE TABLE IF NOT EXISTS public.voucher_lines (
    id                  SERIAL PRIMARY KEY,
    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) ON DELETE CASCADE,

    voucher_id          INTEGER NOT NULL 
                        REFERENCES public.vouchers(id) ON DELETE CASCADE,

    line_no             INTEGER NOT NULL,

    account_id          INTEGER NOT NULL 
                        REFERENCES public.accounts(id) ON DELETE RESTRICT,

    description         TEXT,

    -- Base Currency Amounts
    debit_base          NUMERIC(15,4) DEFAULT 0,
    credit_base         NUMERIC(15,4) DEFAULT 0,

    -- Foreign Currency Amounts
    debit_foreign       NUMERIC(15,4),
    credit_foreign      NUMERIC(15,4),

    -- Tax
    tax_id              INTEGER 
                        REFERENCES public.taxes(id) ON DELETE SET NULL,
    tax_amount_base     NUMERIC(15,4) DEFAULT 0,
    tax_amount_foreign  NUMERIC(15,4),

    -- Commission
    commission_id       INTEGER 
                        REFERENCES public.commissions(id) ON DELETE SET NULL,
    commission_base     NUMERIC(15,4) DEFAULT 0,
    commission_foreign  NUMERIC(15,4),

    -- Line Reference
    reference_type      VARCHAR(30),
    reference_id        INTEGER,
    reference_line_no   INTEGER,

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_deleted          BOOLEAN DEFAULT FALSE,

    CONSTRAINT uq_voucher_line_tenant UNIQUE (voucher_id, line_no, tenant_id)
);

-- Indexes
CREATE INDEX idx_voucher_lines_voucher ON public.voucher_lines(voucher_id);
CREATE INDEX idx_voucher_lines_account ON public.voucher_lines(account_id);
CREATE INDEX idx_voucher_lines_tax ON public.voucher_lines(tax_id);
CREATE INDEX idx_voucher_lines_commission ON public.voucher_lines(commission_id);