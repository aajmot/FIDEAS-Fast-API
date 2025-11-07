DROP TABLE IF EXISTS public.payment_details;
DROP TABLE IF EXISTS public.payments;

CREATE TABLE IF NOT EXISTS public.payments (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    payment_number         VARCHAR(50) NOT NULL,
    payment_date           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Direction
    payment_type           VARCHAR(20) NOT NULL 
                           CHECK (payment_type IN ('RECEIPT', 'PAYMENT', 'CONTRA')),

    -- Party (Customer, Supplier, Employee, Bank, etc.)
    party_type             VARCHAR(20) NOT NULL 
                           CHECK (party_type IN ('CUSTOMER','SUPPLIER','EMPLOYEE','BANK','OTHER')),

    party_id               INTEGER,  -- FK to customers/suppliers/employees

    -- Currency
    base_currency_id       INTEGER NOT NULL 
                           REFERENCES public.currencies(id) ON DELETE RESTRICT,
    foreign_currency_id    INTEGER 
                           REFERENCES public.currencies(id) ON DELETE SET NULL,
    exchange_rate          NUMERIC(15,6) DEFAULT 1,

    -- Amounts
    total_amount_base      NUMERIC(15,4) NOT NULL DEFAULT 0,
    total_amount_foreign   NUMERIC(15,4),

    -- TDS / Advance
    tds_amount_base        NUMERIC(15,4) DEFAULT 0,
    advance_amount_base    NUMERIC(15,4) DEFAULT 0,

    -- Status
    status                 VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
                           CHECK (status IN ('DRAFT','POSTED','CANCELLED','RECONCILED')),

    -- Accounting
    voucher_id             INTEGER 
                           REFERENCES public.vouchers(id) ON DELETE SET NULL,

    -- Metadata
    reference_number       VARCHAR(50),     -- Bank ref, UTR
    remarks                TEXT,
    tags                   TEXT[],

    -- Reconciliation
    is_reconciled          BOOLEAN DEFAULT FALSE,
    reconciled_at          TIMESTAMP,
    reconciled_by          VARCHAR(100),

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_payment_number_tenant 
        UNIQUE (payment_number, tenant_id),

    CONSTRAINT chk_currency_logic 
        CHECK (
            (foreign_currency_id IS NULL AND total_amount_foreign IS NULL AND exchange_rate = 1)
            OR
            (foreign_currency_id IS NOT NULL AND exchange_rate > 0)
        ),

    CONSTRAINT chk_positive_amount 
        CHECK (total_amount_base >= 0)
);

-- Indexes
CREATE INDEX idx_payments_tenant ON public.payments(tenant_id);
CREATE INDEX idx_payments_party ON public.payments(party_type, party_id);
CREATE INDEX idx_payments_date ON public.payments(payment_date);
CREATE INDEX idx_payments_status ON public.payments(status);
CREATE INDEX idx_payments_reconciled ON public.payments(is_reconciled);
CREATE TABLE IF NOT EXISTS public.payment_details (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    payment_id             INTEGER NOT NULL 
                           REFERENCES public.payments(id) ON DELETE CASCADE,

    line_no                INTEGER NOT NULL,

    payment_mode           VARCHAR(20) NOT NULL 
                           CHECK (payment_mode IN ('CASH','BANK','CARD','UPI','CHEQUE','ONLINE','WALLET')),

    -- Bank / Instrument
    bank_account_id        INTEGER 
                           REFERENCES public.bank_accounts(id) ON DELETE SET NULL,

    instrument_number      VARCHAR(50),
    instrument_date        DATE,
    bank_name              VARCHAR(100),
    branch_name            VARCHAR(100),
    ifsc_code              VARCHAR(20),
    transaction_reference  VARCHAR(100),    -- UPI ID, NEFT ref

    -- Amounts
    amount_base            NUMERIC(15,4) NOT NULL,
    amount_foreign         NUMERIC(15,4),

    -- Account (Dr/Cr)
    account_id             INTEGER NOT NULL 
                           REFERENCES public.account_masters(id) ON DELETE RESTRICT,

    description            TEXT,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_payment_detail_line 
        UNIQUE (payment_id, line_no),

    CONSTRAINT chk_amount_positive 
        CHECK (amount_base > 0)
);

-- Indexes
CREATE INDEX idx_payment_details_payment ON public.payment_details(payment_id);
CREATE INDEX idx_payment_details_bank ON public.payment_details(bank_account_id);