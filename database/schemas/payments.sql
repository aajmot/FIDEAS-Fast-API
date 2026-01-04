DROP TABLE IF EXISTS public.payment_allocations;
DROP TABLE IF EXISTS public.payment_details;
DROP TABLE IF EXISTS public.payments;

CREATE TABLE IF NOT EXISTS public.payments (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id              INTEGER
                           REFERENCES public.branches(id) ON DELETE SET NULL,

    payment_number         VARCHAR(50) NOT NULL,
    payment_date           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Direction
    payment_type           VARCHAR(20) NOT NULL 
                           CHECK (payment_type IN ('RECEIPT', 'PAYMENT', 'CONTRA')),

    -- Party (Customer, Supplier, Employee, Bank, etc.)
    party_type             VARCHAR(20) NOT NULL 
                           CHECK (party_type IN ('CUSTOMER','SUPPLIER','EMPLOYEE','BANK','PATIENT','OTHER')),

    party_id               INTEGER,

    -- Document Linking
    source_document_type   VARCHAR(20)
                           CHECK (source_document_type IN ('ORDER','INVOICE','EXPENSE','ADVANCE','BILL','OTHER')),
    source_document_id     INTEGER,

    -- Currency
    base_currency_id       INTEGER NOT NULL 
                           REFERENCES public.currencies(id) ON DELETE RESTRICT,
    foreign_currency_id    INTEGER 
                           REFERENCES public.currencies(id) ON DELETE SET NULL,
    exchange_rate          NUMERIC(15,6) DEFAULT 1,

    -- Amounts
    total_amount_base      NUMERIC(15,4) NOT NULL DEFAULT 0,
    total_amount_foreign   NUMERIC(15,4),

    -- Allocation Tracking
    allocated_amount_base  NUMERIC(15,4) DEFAULT 0,
    unallocated_amount_base NUMERIC(15,4) DEFAULT 0,

    -- TDS / Advance
    tds_amount_base        NUMERIC(15,4) DEFAULT 0,
    advance_amount_base    NUMERIC(15,4) DEFAULT 0,

    -- Refund Handling
    is_refund              BOOLEAN DEFAULT FALSE,
    original_payment_id    INTEGER 
                           REFERENCES public.payments(id) ON DELETE SET NULL,

    -- Status
    status                 VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
                           CHECK (status IN ('DRAFT','POSTED','CANCELLED','RECONCILED')),

    -- Accounting
    voucher_id             INTEGER 
                           REFERENCES public.vouchers(id) ON DELETE SET NULL,

    -- Metadata
    reference_number       VARCHAR(50),
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
        CHECK (total_amount_base >= 0),

    CONSTRAINT chk_allocation_logic
        CHECK (allocated_amount_base + unallocated_amount_base <= total_amount_base)
);

-- Indexes
CREATE INDEX idx_payments_tenant ON public.payments(tenant_id);
CREATE INDEX idx_payments_branch ON public.payments(branch_id);
CREATE INDEX idx_payments_party ON public.payments(party_type, party_id);
CREATE INDEX idx_payments_date ON public.payments(payment_date);
CREATE INDEX idx_payments_status ON public.payments(status);
CREATE INDEX idx_payments_reconciled ON public.payments(is_reconciled);
CREATE INDEX idx_payments_source_doc ON public.payments(source_document_type, source_document_id);
CREATE INDEX idx_payments_refund ON public.payments(is_refund, original_payment_id);


CREATE TABLE IF NOT EXISTS public.payment_details (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id              INTEGER
                           REFERENCES public.branches(id) ON DELETE SET NULL,

    payment_id             INTEGER NOT NULL 
                           REFERENCES public.payments(id) ON DELETE CASCADE,

    line_no                INTEGER NOT NULL,

    payment_mode           VARCHAR(20) NOT NULL 
                           CHECK (payment_mode IN ('CASH','BANK','CARD','UPI','CHEQUE','ONLINE','WALLET','NEFT','RTGS','IMPS')),

    -- Bank / Instrument
    bank_account_id        INTEGER 
                           REFERENCES public.bank_accounts(id) ON DELETE SET NULL,

    instrument_number      VARCHAR(50),
    instrument_date        DATE,
    bank_name              VARCHAR(100),
    branch_name            VARCHAR(100),
    ifsc_code              VARCHAR(20),
    transaction_reference  VARCHAR(100),

    -- Payment Gateway (per line item)
    payment_gateway        VARCHAR(50),
    gateway_transaction_id VARCHAR(100),
    gateway_status         VARCHAR(20),
    gateway_fee_base       NUMERIC(15,4) DEFAULT 0,
    gateway_response       JSONB,

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
CREATE INDEX idx_payment_details_branch ON public.payment_details(branch_id);
CREATE INDEX idx_payment_details_bank ON public.payment_details(bank_account_id);
CREATE INDEX idx_payment_details_mode ON public.payment_details(payment_mode);
CREATE INDEX idx_payment_details_gateway ON public.payment_details(payment_gateway, gateway_transaction_id);


-- Payment Allocations Table
CREATE TABLE IF NOT EXISTS public.payment_allocations (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id              INTEGER
                           REFERENCES public.branches(id) ON DELETE SET NULL,

    payment_id             INTEGER NOT NULL 
                           REFERENCES public.payments(id) ON DELETE CASCADE,

    -- Document Reference
    document_type          VARCHAR(20) NOT NULL
                           CHECK (document_type IN ('ORDER','INVOICE','EXPENSE','BILL','ADVANCE','DEBIT_NOTE','CREDIT_NOTE')),
    document_id            INTEGER NOT NULL,
    document_number        VARCHAR(50),

    -- Allocated Amounts
    allocated_amount_base  NUMERIC(15,4) NOT NULL,
    allocated_amount_foreign NUMERIC(15,4),

    -- Discount/Adjustment
    discount_amount_base   NUMERIC(15,4) DEFAULT 0,
    adjustment_amount_base NUMERIC(15,4) DEFAULT 0,

    -- Metadata
    allocation_date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks                TEXT,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_payment_allocation 
        UNIQUE (payment_id, document_type, document_id),

    CONSTRAINT chk_allocated_positive 
        CHECK (allocated_amount_base > 0)
);

-- Indexes
CREATE INDEX idx_payment_allocations_payment ON public.payment_allocations(payment_id);
CREATE INDEX idx_payment_allocations_branch ON public.payment_allocations(branch_id);
CREATE INDEX idx_payment_allocations_document ON public.payment_allocations(document_type, document_id);
CREATE INDEX idx_payment_allocations_tenant ON public.payment_allocations(tenant_id);
