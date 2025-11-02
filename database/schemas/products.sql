DROP TABLE IF EXISTS public.products;
CREATE TABLE public.products
(
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),

    -- Core Info
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE,
    description TEXT,
    composition TEXT,
    tags TEXT,
    hsn_code VARCHAR(20),           -- For GSTR-1
    schedule VARCHAR(10),           -- H1, H2, etc.
    manufacturer VARCHAR(200),

    -- Category
    category_id INTEGER NOT NULL REFERENCES categories(id),

    -- Unit
    unit_id INTEGER NOT NULL REFERENCES units(id),

    -- === PRICING ===
    mrp_price NUMERIC(12,4) NOT NULL,           -- Maximum Retail Price
    selling_price NUMERIC(12,4) NOT NULL,       -- Base selling price (excl. tax)
    cost_price NUMERIC(12,4) NOT NULL DEFAULT 0, -- For inventory valuation
    is_tax_inclusive BOOLEAN DEFAULT FALSE,     -- Critical for journal

    -- === TAX CONFIGURATION ===
    hsn_id INTEGER REFERENCES hsn_codes(id),    -- Link to HSN master (recommended)
    gst_rate NUMERIC(5,2) DEFAULT 0.00,         -- Total GST % (5,12,18,28)
    cgst_rate NUMERIC(5,2) GENERATED ALWAYS AS (gst_rate / 2) STORED,
    sgst_rate NUMERIC(5,2) GENERATED ALWAYS AS (gst_rate / 2) STORED,
    igst_rate NUMERIC(5,2) DEFAULT 0.00,        -- Override if inter-state
    cess_rate NUMERIC(5,2) DEFAULT 0.00,
    is_reverse_charge BOOLEAN DEFAULT FALSE,    -- RCM
    is_composite BOOLEAN DEFAULT FALSE,         -- Composite scheme

    -- === INVENTORY ===
    is_inventory_item BOOLEAN DEFAULT TRUE,
    reorder_level NUMERIC(10,2) DEFAULT 0,
    danger_level NUMERIC(10,2) DEFAULT 0,
    min_stock NUMERIC(10,2) DEFAULT 0,
    max_stock NUMERIC(10,2) DEFAULT 0,

    -- === COMMISSION & DISCOUNTS ===
    commission_type VARCHAR(20) DEFAULT 'FIXED' 
        CHECK (commission_type IN ('FIXED', 'PERCENTAGE')),
    commission_value NUMERIC(10,2) DEFAULT 0.00,
    max_discount_percent NUMERIC(5,2) DEFAULT 100.00,  -- Prevent over-discount

    -- === TRACKING ===
    barcode VARCHAR(100),
    is_serialized BOOLEAN DEFAULT FALSE,
    warranty_months INTEGER,

    -- === STATUS ===
    is_discontinued BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- === MULTI-CURRENCY (Optional) ===
    currency_id INTEGER REFERENCES currencies(id) DEFAULT 1,  -- 1 = Base
    exchange_rate NUMERIC(12,6) DEFAULT 1.000000,

    -- Audit
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system',
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100) DEFAULT 'system',
    is_deleted BOOLEAN DEFAULT FALSE
);