-- Table: public.ledgers

DROP TABLE IF EXISTS public.ledgers;

CREATE TABLE IF NOT EXISTS public.ledgers
(
    id SERIAL PRIMARY KEY,
    
    tenant_id INTEGER NOT NULL 
        REFERENCES public.tenants(id) ON DELETE CASCADE,
    
    account_id INTEGER NOT NULL 
        REFERENCES public.account_masters(id) ON DELETE RESTRICT,
    
    voucher_id INTEGER NOT NULL 
        REFERENCES public.vouchers(id) ON DELETE CASCADE,
    
    voucher_line_id INTEGER 
        REFERENCES public.voucher_lines(id) ON DELETE CASCADE,
    
    transaction_date TIMESTAMP NOT NULL,
    posting_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Base Currency Amounts (4 decimals for precision)
    debit_amount NUMERIC(15,4) DEFAULT 0 CHECK (debit_amount >= 0),
    credit_amount NUMERIC(15,4) DEFAULT 0 CHECK (credit_amount >= 0),
    
    -- Foreign Currency Support
    currency_id INTEGER 
        REFERENCES public.currencies(id) ON DELETE RESTRICT,
    exchange_rate NUMERIC(15,6) DEFAULT 1,
    debit_foreign NUMERIC(15,4),
    credit_foreign NUMERIC(15,4),
    
    -- Running Balance (Computed)
    balance NUMERIC(15,4),
    
    -- Reference to Source Transaction
    reference_type VARCHAR(30),  -- 'SALES_INVOICE', 'PURCHASE_INVOICE', 'PAYMENT', etc.
    reference_id INTEGER,
    reference_number VARCHAR(50),
    
    narration TEXT,
    
    -- Reconciliation
    is_reconciled BOOLEAN DEFAULT FALSE,
    reconciliation_date TIMESTAMP,
    reconciliation_ref VARCHAR(50),
    
    -- Posting Control
    is_posted BOOLEAN DEFAULT TRUE,
    is_reversal BOOLEAN DEFAULT FALSE,
    reversed_ledger_id INTEGER 
        REFERENCES public.ledgers(id) ON DELETE SET NULL,
    
    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100) DEFAULT 'system',
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    CONSTRAINT chk_debit_credit_exclusive 
        CHECK (
            (debit_amount > 0 AND credit_amount = 0) 
            OR (credit_amount > 0 AND debit_amount = 0)
            OR (debit_amount = 0 AND credit_amount = 0)
        ),
    
    CONSTRAINT chk_foreign_currency_logic 
        CHECK (
            (currency_id IS NULL AND exchange_rate = 1 
                AND debit_foreign IS NULL AND credit_foreign IS NULL)
            OR
            (currency_id IS NOT NULL AND exchange_rate > 0)
        )
);

-- Indexes for Performance
CREATE INDEX idx_ledgers_tenant ON public.ledgers(tenant_id);
CREATE INDEX idx_ledgers_account ON public.ledgers(account_id);
CREATE INDEX idx_ledgers_voucher ON public.ledgers(voucher_id);
CREATE INDEX idx_ledgers_transaction_date ON public.ledgers(transaction_date);
CREATE INDEX idx_ledgers_posting_date ON public.ledgers(posting_date);
CREATE INDEX idx_ledgers_reference ON public.ledgers(reference_type, reference_id);
CREATE INDEX idx_ledgers_reconciliation ON public.ledgers(is_reconciled, account_id) 
    WHERE is_reconciled = FALSE;
CREATE INDEX idx_ledgers_account_date ON public.ledgers(account_id, transaction_date);
CREATE INDEX idx_ledgers_tenant_account_date ON public.ledgers(tenant_id, account_id, transaction_date);