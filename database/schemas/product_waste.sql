DROP TABLE IF EXISTS public.product_waste_items;  -- if exists
DROP TABLE IF EXISTS public.product_waste;        -- if exists (backup first!)

CREATE TABLE IF NOT EXISTS public.product_waste (
    id                  SERIAL PRIMARY KEY,

    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) ON DELETE CASCADE,

    warehouse_id        INTEGER
                        REFERENCES public.warehouses(id) ON DELETE RESTRICT,

    waste_number        VARCHAR(50) NOT NULL,

    waste_date          TIMESTAMP WITHOUT TIME ZONE NOT NULL 
                        DEFAULT CURRENT_TIMESTAMP,

    reason              VARCHAR(500) NOT NULL,  -- General reason (e.g., "Monthly Cleanup")

    -- Totals (auto-calculated from items)
    total_quantity      NUMERIC(15,4) NOT NULL DEFAULT 0,
    total_cost_base     NUMERIC(15,4) NOT NULL DEFAULT 0,
    total_cost_foreign  NUMERIC(15,4),

    -- Optional foreign currency for the whole document
    currency_id         INTEGER 
                        REFERENCES public.currencies(id) ON DELETE SET NULL,
    exchange_rate       NUMERIC(15,4) DEFAULT 1,

    -- Accounting
    voucher_id          INTEGER 
                        REFERENCES public.vouchers(id) ON DELETE SET NULL,

    -- Audit
    created_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_active           BOOLEAN DEFAULT TRUE,
    is_deleted          BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_waste_number_tenant_warehouse 
        UNIQUE (waste_number, tenant_id, warehouse_id),

    CONSTRAINT chk_currency_logic 
        CHECK (
            (currency_id IS NULL AND total_cost_foreign IS NULL AND exchange_rate = 1)
            OR
            (currency_id IS NOT NULL AND exchange_rate > 0)
        )
);

-- Indexes
CREATE INDEX idx_product_waste_tenant ON public.product_waste(tenant_id);
CREATE INDEX idx_product_waste_warehouse ON public.product_waste(warehouse_id);
CREATE INDEX idx_product_waste_date ON public.product_waste(waste_date);
CREATE INDEX idx_product_waste_voucher ON public.product_waste(voucher_id);


CREATE TABLE IF NOT EXISTS public.product_waste_items (
    id                  SERIAL PRIMARY KEY,

    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) ON DELETE CASCADE,

    waste_id            INTEGER NOT NULL 
                        REFERENCES public.product_waste(id) ON DELETE CASCADE,

    line_no             INTEGER NOT NULL,  -- Sequential per waste

    product_id          INTEGER NOT NULL 
                        REFERENCES public.products(id) ON DELETE RESTRICT,

    batch_number        VARCHAR(50),

    -- Quantity
    quantity            NUMERIC(12,4) NOT NULL CHECK (quantity > 0),

    -- Cost in Base Currency
    unit_cost_base      NUMERIC(15,4) NOT NULL CHECK (unit_cost_base >= 0),
    total_cost_base     NUMERIC(15,4) NOT NULL CHECK (total_cost_base >= 0),

    -- Optional: Foreign Currency (per item)
    currency_id         INTEGER 
                        REFERENCES public.currencies(id) ON DELETE SET NULL,
    unit_cost_foreign   NUMERIC(15,4),
    total_cost_foreign  NUMERIC(15,4),
    exchange_rate       NUMERIC(15,4) DEFAULT 1,

    -- Item-level reason (optional, overrides header)
    reason              VARCHAR(500),

    -- Audit
    created_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_deleted          BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_waste_item_line UNIQUE (waste_id, line_no),
    
    CONSTRAINT chk_item_total_cost 
        CHECK (total_cost_base = ROUND(quantity * unit_cost_base, 4)),

    CONSTRAINT chk_item_foreign_cost 
        CHECK (
            total_cost_foreign IS NULL 
            OR total_cost_foreign = ROUND(quantity * unit_cost_foreign, 4)
        ),

    CONSTRAINT chk_item_currency_logic 
        CHECK (
            (currency_id IS NULL 
                AND unit_cost_foreign IS NULL 
                AND total_cost_foreign IS NULL 
                AND exchange_rate = 1)
            OR
            (currency_id IS NOT NULL AND exchange_rate > 0)
        )
);

-- Indexes
CREATE INDEX idx_waste_items_waste ON public.product_waste_items(waste_id);
CREATE INDEX idx_waste_items_product ON public.product_waste_items(product_id);
CREATE INDEX idx_waste_items_tenant ON public.product_waste_items(tenant_id);