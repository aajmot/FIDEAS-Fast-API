
DROP TABLE IF EXISTS public.credit_note_items;
DROP TABLE IF EXISTS public.credit_notes;

CREATE TABLE IF NOT EXISTS public.credit_notes (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    note_number            VARCHAR(50) NOT NULL,
    reference_number       VARCHAR(50),                     -- Internal reference

    note_date              DATE NOT NULL,
    due_date               DATE,

    customer_id            INTEGER NOT NULL 
                           REFERENCES public.customers(id) ON DELETE RESTRICT,

    original_invoice_id    INTEGER 
                           REFERENCES public.sales_invoices(id) ON DELETE SET NULL,

    original_invoice_number VARCHAR(50),

    -- === Currency ===
    base_currency_id       INTEGER NOT NULL 
                           REFERENCES public.currencies(id) ON DELETE RESTRICT,
    foreign_currency_id    INTEGER 
                           REFERENCES public.currencies(id) ON DELETE SET NULL,
    exchange_rate          NUMERIC(15,6) DEFAULT 1,

    -- === GST Summary ===
    cgst_amount_base       NUMERIC(15,4) DEFAULT 0,
    sgst_amount_base       NUMERIC(15,4) DEFAULT 0,
    igst_amount_base       NUMERIC(15,4) DEFAULT 0,
    cess_amount_base       NUMERIC(15,4) DEFAULT 0,

    -- === Totals (Base) ===
    subtotal_base          NUMERIC(15,4) DEFAULT 0,
    discount_amount_base   NUMERIC(15,4) DEFAULT 0,
    tax_amount_base        NUMERIC(15,4) DEFAULT 0,
    total_amount_base      NUMERIC(15,4) NOT NULL DEFAULT 0,

    -- === Totals (Foreign) ===
    subtotal_foreign       NUMERIC(15,4),
    discount_amount_foreign NUMERIC(15,4),
    tax_amount_foreign     NUMERIC(15,4),
    total_amount_foreign   NUMERIC(15,4),

    -- === Status ===
    status                 VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
                           CHECK (status IN ('DRAFT','POSTED','APPLIED','CANCELLED')),

    credit_note_type       VARCHAR(20) NOT NULL DEFAULT 'SALES_RETURN'
                           CHECK (credit_note_type IN ('SALES_RETURN','PRICE_ADJUSTMENT','DISCOUNT','OTHER')),

    -- === Accounting ===
    voucher_id             INTEGER 
                           REFERENCES public.vouchers(id) ON DELETE SET NULL,

    -- === Metadata ===
    reason                 TEXT NOT NULL,
    notes                  TEXT,
    tags                   TEXT[],

    -- === Audit ===
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- === Constraints ===
    CONSTRAINT uq_credit_note_number_tenant 
        UNIQUE (note_number, tenant_id),

    CONSTRAINT chk_currency_logic 
        CHECK (
            (foreign_currency_id IS NULL 
                AND exchange_rate = 1 
                AND subtotal_foreign IS NULL 
                AND total_amount_foreign IS NULL)
            OR
            (foreign_currency_id IS NOT NULL AND exchange_rate > 0)
        ),

    CONSTRAINT chk_due_date 
        CHECK (due_date IS NULL OR due_date >= note_date),

    CONSTRAINT chk_gst_sum 
        CHECK (ABS(tax_amount_base - (cgst_amount_base + sgst_amount_base + igst_amount_base + cess_amount_base)) < 0.01),

    CONSTRAINT chk_total_amount_positive
        CHECK (total_amount_base >= 0)
);

-- Indexes
CREATE INDEX idx_credit_note_tenant ON public.credit_notes(tenant_id);
CREATE INDEX idx_credit_note_customer ON public.credit_notes(customer_id);
CREATE INDEX idx_credit_note_date ON public.credit_notes(note_date);
CREATE INDEX idx_credit_note_status ON public.credit_notes(status);
CREATE INDEX idx_credit_note_original_invoice ON public.credit_notes(original_invoice_id);

CREATE TABLE IF NOT EXISTS public.credit_note_items (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    credit_note_id         INTEGER NOT NULL 
                           REFERENCES public.credit_notes(id) ON DELETE CASCADE,

    line_no                INTEGER NOT NULL,

    product_id             INTEGER NOT NULL 
                           REFERENCES public.products(id) ON DELETE RESTRICT,

    description            TEXT,
    hsn_code               VARCHAR(20),
    batch_number           VARCHAR(50),
    serial_numbers         TEXT,

    -- === Quantity ===
    quantity               NUMERIC(15,4) NOT NULL CHECK (quantity > 0),
    free_quantity          NUMERIC(15,4) DEFAULT 0,
    uom                    VARCHAR(20) DEFAULT 'NOS',

    -- === Pricing (Base) ===
    unit_price_base        NUMERIC(15,4) NOT NULL CHECK (unit_price_base >= 0),
    discount_percent       NUMERIC(5,2) DEFAULT 0,
    discount_amount_base   NUMERIC(15,4) DEFAULT 0,
    taxable_amount_base    NUMERIC(15,4) NOT NULL,

    -- === GST ===
    cgst_rate              NUMERIC(5,2) DEFAULT 0,
    cgst_amount_base       NUMERIC(15,4) DEFAULT 0,
    sgst_rate              NUMERIC(5,2) DEFAULT 0,
    sgst_amount_base       NUMERIC(15,4) DEFAULT 0,
    igst_rate              NUMERIC(5,2) DEFAULT 0,
    igst_amount_base       NUMERIC(15,4) DEFAULT 0,
    cess_rate              NUMERIC(5,2) DEFAULT 0,
    cess_amount_base       NUMERIC(15,4) DEFAULT 0,
    tax_amount_base        NUMERIC(15,4) DEFAULT 0,

    -- === Total ===
    total_amount_base      NUMERIC(15,4) NOT NULL,

    -- === Foreign Currency ===
    unit_price_foreign     NUMERIC(15,4),
    discount_amount_foreign NUMERIC(15,4),
    taxable_amount_foreign NUMERIC(15,4),
    tax_amount_foreign     NUMERIC(15,4),
    total_amount_foreign   NUMERIC(15,4),

    -- === Audit ===
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- === Constraints ===
    CONSTRAINT uq_credit_note_item_line 
        UNIQUE (credit_note_id, line_no),

    CONSTRAINT chk_credit_note_item_line_total 
        CHECK (total_amount_base = ROUND(taxable_amount_base + tax_amount_base, 4)),

    CONSTRAINT chk_credit_note_item_gst_exclusivity 
        CHECK (
            (cgst_amount_base > 0 AND sgst_amount_base > 0 AND igst_amount_base = 0)
            OR (igst_amount_base > 0 AND cgst_amount_base = 0 AND sgst_amount_base = 0)
            OR (cgst_amount_base = 0 AND sgst_amount_base = 0 AND igst_amount_base = 0)
        )
);

-- Indexes
CREATE INDEX idx_credit_note_item_credit_note ON public.credit_note_items(credit_note_id);
CREATE INDEX idx_credit_note_item_product ON public.credit_note_items(product_id);
