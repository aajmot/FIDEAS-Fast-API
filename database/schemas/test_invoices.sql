DROP TABLE IF EXISTS public.payment_allocations;
DROP TABLE IF EXISTS public.test_invoice_items;
DROP TABLE IF EXISTS public.test_invoices;

CREATE TABLE IF NOT EXISTS public.test_invoices (
    id                     SERIAL PRIMARY KEY,
    
    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id              INTEGER
                           REFERENCES public.branches(id) ON DELETE SET NULL,

    -- Invoice Info
    invoice_number         VARCHAR(50) NOT NULL,
    invoice_date           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date               DATE,

    -- Related Order
    test_order_id          INTEGER NOT NULL
                           REFERENCES public.test_orders(id) ON DELETE RESTRICT,

    -- Patient
    patient_id             INTEGER 
                           REFERENCES public.patients(id) ON DELETE SET NULL,
    patient_name           VARCHAR(200) NOT NULL,
    patient_phone          VARCHAR(20) NOT NULL,

    -- Amounts
    subtotal_amount        NUMERIC(12,4) NOT NULL DEFAULT 0,
    items_total_discount_amount NUMERIC(12,4) DEFAULT 0,
    taxable_amount         NUMERIC(12,4) NOT NULL DEFAULT 0,

    cgst_amount            NUMERIC(12,4) DEFAULT 0,
    sgst_amount            NUMERIC(12,4) DEFAULT 0,
    igst_amount            NUMERIC(12,4) DEFAULT 0,
    cess_amount            NUMERIC(12,4) DEFAULT 0,
    
    total_tax_amount       NUMERIC(12,4) GENERATED ALWAYS AS 
                           (cgst_amount + sgst_amount + igst_amount + cess_amount) STORED,

    overall_disc_percentage NUMERIC(5,4) NOT NULL DEFAULT 0,
    overall_disc_amount     NUMERIC(12,4) NOT NULL DEFAULT 0,
    
    roundoff               NUMERIC(12,4) DEFAULT 0,
    final_amount           NUMERIC(12,4) NOT NULL,

    -- Payment Tracking
    paid_amount            NUMERIC(12,4) NOT NULL DEFAULT 0,
    balance_amount         NUMERIC(12,4) GENERATED ALWAYS AS 
                           (final_amount - paid_amount) STORED,

    -- Status
    payment_status         VARCHAR(20) DEFAULT 'UNPAID'
                           CHECK (payment_status IN ('UNPAID','PARTIAL','PAID','OVERPAID')),
    
    status                 VARCHAR(20) DEFAULT 'DRAFT'
                           CHECK (status IN ('DRAFT','POSTED','CANCELLED')),

    -- Accounting
    voucher_id             INTEGER 
                           REFERENCES public.vouchers(id) ON DELETE SET NULL,

    -- Notes
    notes                  TEXT,
    tags                   TEXT[],

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_invoice_number_tenant_test_invoices 
        UNIQUE (invoice_number, tenant_id),

    CONSTRAINT chk_invoice_amounts_test_invoices 
        CHECK (final_amount >= 0 AND paid_amount >= 0)
);

-- Indexes
CREATE INDEX idx_test_invoices_tenant ON public.test_invoices(tenant_id);
CREATE INDEX idx_test_invoices_order ON public.test_invoices(test_order_id);
CREATE INDEX idx_test_invoices_patient ON public.test_invoices(patient_id);
CREATE INDEX idx_test_invoices_status ON public.test_invoices(status);
CREATE INDEX idx_test_invoices_payment_status ON public.test_invoices(payment_status);
CREATE INDEX idx_test_invoices_date ON public.test_invoices(invoice_date);


CREATE TABLE IF NOT EXISTS public.test_invoice_items (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    test_invoice_id        INTEGER NOT NULL 
                           REFERENCES public.test_invoices(id) ON DELETE CASCADE,

    line_no                INTEGER NOT NULL,

    -- Test or Panel
    test_id                INTEGER 
                           REFERENCES public.tests(id) ON DELETE RESTRICT,
    test_name              VARCHAR(200),
    
    panel_id               INTEGER 
                           REFERENCES public.test_panels(id) ON DELETE RESTRICT,
    panel_name             VARCHAR(200),

    -- Pricing
    rate                   NUMERIC(12,4) NOT NULL,
    disc_percentage        NUMERIC(5,2) DEFAULT 0,
    disc_amount            NUMERIC(12,4) DEFAULT 0,
    
    taxable_amount         NUMERIC(12,4) NOT NULL,
    cgst_rate              NUMERIC(5,2) DEFAULT 0,
    cgst_amount            NUMERIC(12,4) DEFAULT 0,
    sgst_rate              NUMERIC(5,2) DEFAULT 0,
    sgst_amount            NUMERIC(12,4) DEFAULT 0,
    igst_rate              NUMERIC(5,2) DEFAULT 0,
    igst_amount            NUMERIC(12,4) DEFAULT 0,
    cess_rate              NUMERIC(5,2) DEFAULT 0,
    cess_amount            NUMERIC(12,4) DEFAULT 0,
    
    total_amount           NUMERIC(12,4) NOT NULL,

    remarks                TEXT,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_test_invoice_item_line 
        UNIQUE (test_invoice_id, line_no),

    CONSTRAINT chk_invoice_item_amount 
        CHECK (total_amount >= 0)
);

-- Indexes
CREATE INDEX idx_test_invoice_items_invoice ON public.test_invoice_items(test_invoice_id);
CREATE INDEX idx_test_invoice_items_test ON public.test_invoice_items(test_id);
CREATE INDEX idx_test_invoice_items_panel ON public.test_invoice_items(panel_id);


-- Add after payment_details table

CREATE TABLE IF NOT EXISTS public.payment_allocations (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    payment_id             INTEGER NOT NULL 
                           REFERENCES public.payments(id) ON DELETE CASCADE,

    -- Invoice Reference
    invoice_type           VARCHAR(20) NOT NULL 
                           CHECK (invoice_type IN ('TEST_INVOICE','SALES_INVOICE','PURCHASE_INVOICE','CREDIT_NOTE','DEBIT_NOTE')),
    
    invoice_id             INTEGER NOT NULL,  -- FK to respective invoice tables
	invoice_number			VARCHAR(20) NOT NULL,

    -- Allocation
    allocated_amount       NUMERIC(15,4) NOT NULL,

    remarks                TEXT,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,

    CONSTRAINT chk_allocated_amount_positive 
        CHECK (allocated_amount > 0)
);

-- Indexes
CREATE INDEX idx_payment_allocations_payment ON public.payment_allocations(payment_id);
CREATE INDEX idx_payment_allocations_invoice ON public.payment_allocations(invoice_type, invoice_id);
