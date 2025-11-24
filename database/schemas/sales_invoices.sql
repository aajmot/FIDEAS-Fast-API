DROP TABLE IF EXISTS public.sales_invoice_items;
DROP TABLE IF EXISTS public.sales_invoices;

CREATE TABLE IF NOT EXISTS public.sales_invoices (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    invoice_number         VARCHAR(50) NOT NULL,
    reference_number       VARCHAR(50),                     -- Customer PO

    invoice_date           DATE NOT NULL,
    due_date               DATE,

    customer_id            INTEGER NOT NULL 
                           REFERENCES public.customers(id) ON DELETE RESTRICT,

    sales_order_id         INTEGER 
                           REFERENCES public.sales_orders(id) ON DELETE SET NULL,

    payment_term_id        INTEGER 
                           REFERENCES public.payment_terms(id) ON DELETE SET NULL,

    warehouse_id           INTEGER NOT NULL 
                           REFERENCES public.warehouses(id) ON DELETE RESTRICT,

    shipping_address_id    INTEGER 
                           REFERENCES public.addresses(id) ON DELETE SET NULL,

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

    -- === Payment ===
    paid_amount_base       NUMERIC(15,4) DEFAULT 0,
    balance_amount_base    NUMERIC(15,4) DEFAULT 0,

    -- === Status ===
    status                 VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
                           CHECK (status IN ('DRAFT','POSTED','PAID','PARTIALLY_PAID','CANCELLED','CREDIT_NOTE')),

    invoice_type           VARCHAR(20) NOT NULL DEFAULT 'TAX_INVOICE'
                           CHECK (invoice_type IN ('TAX_INVOICE','BILL_OF_SUPPLY','EXPORT','CREDIT_NOTE')),

    -- === e-Invoice ===
    is_einvoice            BOOLEAN DEFAULT FALSE,
    einvoice_irn           VARCHAR(100),
    einvoice_ack_no        VARCHAR(50),
    einvoice_ack_date      TIMESTAMP,
    einvoice_qr_code       TEXT,
    einvoice_status        VARCHAR(20) DEFAULT 'PENDING'
                           CHECK (einvoice_status IN ('PENDING','GENERATED','CANCELLED','FAILED')),

    -- === e-Way Bill ===
    eway_bill_no           VARCHAR(50),
    eway_bill_date         TIMESTAMP,
    eway_bill_valid_till   TIMESTAMP,

    -- === Accounting ===
    voucher_id             INTEGER 
                           REFERENCES public.vouchers(id) ON DELETE SET NULL,

    -- === Metadata ===
    notes                  TEXT,
    terms_conditions       TEXT,
    tags                   TEXT[],

    -- === Audit ===
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- === Constraints ===
    CONSTRAINT uq_sales_invoice_number_tenant 
        UNIQUE (invoice_number, tenant_id),

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
        CHECK (due_date IS NULL OR due_date >= invoice_date),

    CONSTRAINT chk_gst_sum 
        CHECK (ABS(tax_amount_base - (cgst_amount_base + sgst_amount_base + igst_amount_base + cess_amount_base)) < 0.01)
);

-- Indexes
CREATE INDEX idx_sales_invoice_tenant ON public.sales_invoices(tenant_id);
CREATE INDEX idx_sales_invoice_customer ON public.sales_invoices(customer_id);
CREATE INDEX idx_sales_invoice_date ON public.sales_invoices(invoice_date);
CREATE INDEX idx_sales_invoice_status ON public.sales_invoices(status);
CREATE INDEX idx_sales_invoice_einvoice ON public.sales_invoices(einvoice_irn);

CREATE TABLE IF NOT EXISTS public.sales_invoice_items (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    invoice_id             INTEGER NOT NULL 
                           REFERENCES public.sales_invoices(id) ON DELETE CASCADE,

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
    unit_cost_base         NUMERIC(15,4) NOT NULL CHECK (unit_cost_base >= 0),  -- For COGS
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
    CONSTRAINT uq_sales_invoice_item_line 
        UNIQUE (invoice_id, line_no),

    CONSTRAINT chk_sales_invoice_item_line_total 
        CHECK (total_amount_base = ROUND(taxable_amount_base + tax_amount_base, 4)),

    CONSTRAINT chk_sales_invoice_item_gst_exclusivity 
        CHECK (
            (cgst_amount_base > 0 AND sgst_amount_base > 0 AND igst_amount_base = 0)
            OR (igst_amount_base > 0 AND cgst_amount_base = 0 AND sgst_amount_base = 0)
            OR (cgst_amount_base = 0 AND sgst_amount_base = 0 AND igst_amount_base = 0)
        )
);

-- Indexes
CREATE INDEX idx_sales_item_invoice ON public.sales_invoice_items(invoice_id);
CREATE INDEX idx_sales_item_product ON public.sales_invoice_items(product_id);