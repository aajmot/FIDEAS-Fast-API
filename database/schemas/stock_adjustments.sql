DROP TABLE IF EXISTS public.stock_adjustment_items;
DROP TABLE IF EXISTS public.stock_adjustments;

CREATE TABLE IF NOT EXISTS public.stock_adjustments (
    id                  SERIAL PRIMARY KEY,

    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) ON DELETE CASCADE,

    warehouse_id        INTEGER NOT NULL 
                        REFERENCES public.warehouses(id) ON DELETE RESTRICT,

    adjustment_number   VARCHAR(50) NOT NULL,

    adjustment_date     TIMESTAMP WITHOUT TIME ZONE NOT NULL 
                        DEFAULT CURRENT_TIMESTAMP,

    adjustment_type     VARCHAR(20) NOT NULL 
                        CHECK (adjustment_type IN ('PHYSICAL', 'DAMAGED', 'THEFT', 'OTHER')),

    reason              VARCHAR(500) NOT NULL,

    -- Totals (auto-calculated)
    total_items         INTEGER NOT NULL DEFAULT 0,
    net_quantity_change NUMERIC(15,4) NOT NULL DEFAULT 0,
    total_cost_impact   NUMERIC(15,4) NOT NULL DEFAULT 0,

    -- Optional foreign currency
    currency_id         INTEGER REFERENCES public.currencies(id),
    exchange_rate       NUMERIC(15,4) DEFAULT 1,

    -- Accounting
    voucher_id          INTEGER REFERENCES public.vouchers(id) ON DELETE SET NULL,

    -- Audit
    created_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_active           BOOLEAN DEFAULT TRUE,
    is_deleted          BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_adjustment_number_tenant 
        UNIQUE (adjustment_number, tenant_id),

    CONSTRAINT chk_currency_logic 
        CHECK (
            (currency_id IS NULL AND exchange_rate = 1)
            OR (currency_id IS NOT NULL AND exchange_rate > 0)
        )
);

-- Indexes
CREATE INDEX idx_stock_adj_tenant ON public.stock_adjustments(tenant_id);
CREATE INDEX idx_stock_adj_warehouse ON public.stock_adjustments(warehouse_id);
CREATE INDEX idx_stock_adj_date ON public.stock_adjustments(adjustment_date);
CREATE INDEX idx_stock_adj_voucher ON public.stock_adjustments(voucher_id);


CREATE TABLE IF NOT EXISTS public.stock_adjustment_items (
    id                  SERIAL PRIMARY KEY,

    tenant_id           INTEGER NOT NULL 
                        REFERENCES public.tenants(id) ON DELETE CASCADE,

    adjustment_id       INTEGER NOT NULL 
                        REFERENCES public.stock_adjustments(id) ON DELETE CASCADE,

    line_no             INTEGER NOT NULL,

    product_id          INTEGER NOT NULL 
                        REFERENCES public.products(id) ON DELETE RESTRICT,

    batch_number        VARCHAR(50),

    -- Adjustment Direction & Quantity
    adjustment_qty      NUMERIC(12,4) NOT NULL,  -- +ve = increase, -ve = decrease
    uom                 VARCHAR(20) NOT NULL DEFAULT 'NOS',

    -- Current stock (before adjustment) - for audit
    stock_before        NUMERIC(12,4) NOT NULL DEFAULT 0,
    stock_after         NUMERIC(12,4) NOT NULL DEFAULT 0,

    -- Cost
    unit_cost_base      NUMERIC(15,4) NOT NULL CHECK (unit_cost_base >= 0),
    cost_impact         NUMERIC(15,4) NOT NULL,  -- = adjustment_qty * unit_cost_base

    -- Optional foreign currency
    currency_id         INTEGER REFERENCES public.currencies(id),
    unit_cost_foreign   NUMERIC(15,4),
    cost_impact_foreign NUMERIC(15,4),
    exchange_rate       NUMERIC(15,4) DEFAULT 1,

    -- Optional line reason
    reason              VARCHAR(500),

    -- Audit
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_deleted          BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_adj_item_line UNIQUE (adjustment_id, line_no),
    
    CONSTRAINT chk_cost_impact 
        CHECK (cost_impact = ROUND(adjustment_qty * unit_cost_base, 4)),

    CONSTRAINT chk_foreign_cost 
        CHECK (
            cost_impact_foreign IS NULL 
            OR cost_impact_foreign = ROUND(adjustment_qty * unit_cost_foreign, 4)
        ),

    CONSTRAINT chk_currency_logic 
        CHECK (
            (currency_id IS NULL 
                AND unit_cost_foreign IS NULL 
                AND cost_impact_foreign IS NULL 
                AND exchange_rate = 1)
            OR
            (currency_id IS NOT NULL AND exchange_rate > 0)
        )
);

-- Indexes
CREATE INDEX idx_adj_items_adj ON public.stock_adjustment_items(adjustment_id);
CREATE INDEX idx_adj_items_product ON public.stock_adjustment_items(product_id);