DROP TABLE IF EXISTS public.purchase_order_items;
DROP TABLE IF EXISTS public.purchase_orders;

CREATE TABLE public.purchase_orders
(
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),

    -- PO Info
    po_number VARCHAR(50) NOT NULL UNIQUE,
    reference_number VARCHAR(100),  -- Supplier PO/Quote
    order_date TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),

    -- Supplier
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    supplier_name VARCHAR(200),
    supplier_gstin VARCHAR(15),
    supplier_address VARCHAR(200),

    -- === AMOUNT BREAKDOWN ===
    subtotal_amount NUMERIC(12,4) NOT NULL DEFAULT 0,           -- Sum of line total_price
    header_discount_percent NUMERIC(5,2) DEFAULT 0,
    header_discount_amount NUMERIC(12,4) DEFAULT 0,

    taxable_amount NUMERIC(12,4) NOT NULL DEFAULT 0,            -- After all discounts
    cgst_amount NUMERIC(12,4) DEFAULT 0,
    sgst_amount NUMERIC(12,4) DEFAULT 0,
    igst_amount NUMERIC(12,4) DEFAULT 0,
    utgst_amount NUMERIC(12,4) DEFAULT 0,
    cess_amount NUMERIC(12,4) DEFAULT 0,
    

    total_tax_amount NUMERIC(12,4) GENERATED ALWAYS AS 
        (cgst_amount + sgst_amount + igst_amount + utgst_amount + cess_amount) STORED,

    roundoff NUMERIC(12,4) DEFAULT 0,
    net_amount NUMERIC(12,4) NOT NULL,  -- Final payable

    -- === MULTI-CURRENCY ===
    currency_id INTEGER REFERENCES currencies(id) DEFAULT 1,
    exchange_rate NUMERIC(12,6) DEFAULT 1.000000,
    net_amount_base NUMERIC(12,4) GENERATED ALWAYS AS 
        (net_amount * exchange_rate) STORED,

    -- === TAX & RCM ===
    is_reverse_charge BOOLEAN DEFAULT FALSE,
    is_tax_inclusive BOOLEAN DEFAULT FALSE,  -- Purchase price includes GST?

    -- Status
    status VARCHAR(20) DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT','APPROVED','RECEIVED','BILLED','CANCELLED','REVERSED')),
    approval_status VARCHAR(20) DEFAULT 'DRAFT',
    approval_request_id INTEGER,

    -- Reversal
    reversal_reason TEXT,
    reversed_at TIMESTAMP WITHOUT TIME ZONE,
    reversed_by VARCHAR(100),

    -- Audit
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system',
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100) DEFAULT 'system',
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE public.purchase_order_items
(
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),

    purchase_order_id INTEGER NOT NULL 
        REFERENCES purchase_orders(id) ON DELETE CASCADE,

    -- Product
    product_id INTEGER NOT NULL REFERENCES products(id),
    product_name VARCHAR(200) NOT NULL,
    hsn_code VARCHAR(20),
    description TEXT,

    -- Quantity
    quantity NUMERIC(10,2) NOT NULL DEFAULT 0,
    free_quantity NUMERIC(10,2) DEFAULT 0,

    -- Pricing
    mrp NUMERIC(12,4),
    unit_price NUMERIC(12,4) NOT NULL,           -- After line discount
    line_discount_percent NUMERIC(5,2) DEFAULT 0,
    line_discount_amount NUMERIC(12,4) DEFAULT 0,

    -- === TAX BREAKDOWN (Per Line) ===
    taxable_amount NUMERIC(12,4) NOT NULL,       -- (qty * unit_price) - discount
    cgst_rate NUMERIC(5,2) DEFAULT 0,
    cgst_amount NUMERIC(12,4) DEFAULT 0,
    sgst_rate NUMERIC(5,2) DEFAULT 0,
    sgst_amount NUMERIC(12,4) DEFAULT 0,
    igst_rate NUMERIC(5,2) DEFAULT 0,
    igst_amount NUMERIC(12,4) DEFAULT 0,
    ugst_rate NUMERIC(5,2) DEFAULT 0,
    ugst_amount NUMERIC(12,4) DEFAULT 0,
    cess_rate NUMERIC(5,2) DEFAULT 0,
    cess_amount NUMERIC(12,4) DEFAULT 0,

    total_price NUMERIC(12,4) NOT NULL,          -- taxable + tax

    -- Batch & Tracking
    batch_number VARCHAR(50),
    expiry_date DATE,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system',
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100) DEFAULT 'system',
    is_deleted BOOLEAN DEFAULT FALSE
);