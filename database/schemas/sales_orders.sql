DROP TABLE IF EXISTS public.sales_orders;
CREATE TABLE public.sales_orders
(
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),

    -- Order Info
    order_date TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    order_number VARCHAR(50) NOT NULL UNIQUE,
    reference_number VARCHAR(100),  -- Invoice/PO reference

    -- Customer
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    customer_name VARCHAR(200),
    customer_phone VARCHAR(20),
    agency_id INTEGER REFERENCES agencies(id),

    -- === AMOUNT BREAKDOWN (Critical for Journal) ===
    subtotal_amount NUMERIC(12,4) NOT NULL DEFAULT 0,        -- Sum of line total_price (before discount)
    header_discount_percent NUMERIC(5,2) DEFAULT 0,
    header_discount_amount NUMERIC(12,4) DEFAULT 0,

    taxable_amount NUMERIC(12,4) NOT NULL DEFAULT 0,         -- After all discounts
    cgst_amount NUMERIC(12,4) DEFAULT 0,
    sgst_amount NUMERIC(12,4) DEFAULT 0,
    igst_amount NUMERIC(12,4) DEFAULT 0,
    utgst_amount NUMERIC(12,4) DEFAULT 0,

    total_tax_amount NUMERIC(12,4) GENERATED ALWAYS AS 
        (cgst_amount + sgst_amount + igst_amount + utgst_amount) STORED,
    
    agent_commission_percent NUMERIC(5,2),
    agent_commission_amount NUMERIC(12,4) DEFAULT 0,
    
    roundoff NUMERIC(12,4) DEFAULT 0,
    net_amount NUMERIC(12,4) NOT NULL,  -- Final payable = taxable + tax + roundoff
    
    -- === MULTI-CURRENCY ===
    currency_id INTEGER REFERENCES currencies(id) DEFAULT 1,  -- 1 = Base (INR)
    exchange_rate NUMERIC(12,6) DEFAULT 1.000000,
    net_amount_base NUMERIC(12,4) GENERATED ALWAYS AS 
        (net_amount * exchange_rate) STORED,

    -- Status & Reversal
    status VARCHAR(20) DEFAULT 'DRAFT' 
        CHECK (status IN ('DRAFT','ORDERED','APPROVED','INVOICED','CANCELLED','REVERSED')),
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


DROP TABLE IF EXISTS public.sales_order_items;
CREATE TABLE public.sales_order_items
(
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),

    sales_order_id INTEGER NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,

    -- Product
    product_id INTEGER NOT NULL REFERENCES products(id),
    product_name VARCHAR(200) NOT NULL,
    batch_number VARCHAR(100),
    expiry_date DATE,

    -- Quantity
    quantity NUMERIC(10,2) NOT NULL DEFAULT 0,
    free_quantity NUMERIC(10,2) DEFAULT 0,

    -- Pricing
    mrp_price NUMERIC(12,4),
    unit_price NUMERIC(12,4) NOT NULL,        -- After line discount
    line_discount_percent NUMERIC(5,2) DEFAULT 0,
    line_discount_amount NUMERIC(12,4) DEFAULT 0,

    -- === TAX BREAKDOWN (Per Line) ===
    taxable_amount NUMERIC(12,4) NOT NULL,    -- (qty * unit_price) - line_discount
    cgst_rate NUMERIC(5,2) DEFAULT 0,
    cgst_amount NUMERIC(12,4) DEFAULT 0,
    sgst_rate NUMERIC(5,2) DEFAULT 0,
    sgst_amount NUMERIC(12,4) DEFAULT 0,
    igst_rate NUMERIC(5,2) DEFAULT 0,
    igst_amount NUMERIC(12,4) DEFAULT 0,
    utgst_rate NUMERIC(5,2) DEFAULT 0,
    utgst_amount NUMERIC(12,4) DEFAULT 0,


    agent_commission_percent NUMERIC(5,2),
    agent_commission_amount NUMERIC(12,4) DEFAULT 0,

    

    total_price NUMERIC(12,4) NOT NULL,       -- taxable + tax

    -- Narration (optional)
    narration TEXT,

    -- Audit
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system',
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100) DEFAULT 'system',
    is_deleted BOOLEAN DEFAULT FALSE
);