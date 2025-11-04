DROP TABLE IF EXISTS public.stock_transfer_items;
DROP TABLE IF EXISTS public.stock_transfers;

CREATE TABLE IF NOT EXISTS public.stock_transfers (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    transfer_number        VARCHAR(50) NOT NULL,

    from_warehouse_id      INTEGER NOT NULL 
                           REFERENCES public.warehouses(id) ON DELETE RESTRICT,

    to_warehouse_id        INTEGER NOT NULL 
                           REFERENCES public.warehouses(id) ON DELETE RESTRICT,

    transfer_date          TIMESTAMP WITHOUT TIME ZONE NOT NULL 
                           DEFAULT CURRENT_TIMESTAMP,

    transfer_type          VARCHAR(20) NOT NULL 
                           CHECK (transfer_type IN ('INTERNAL', 'INTERCOMPANY', 'RETURN')),

    reason                 VARCHAR(500),

    -- Totals
    total_items            INTEGER NOT NULL DEFAULT 0,
    total_quantity         NUMERIC(15,4) NOT NULL DEFAULT 0,
    total_cost_base        NUMERIC(15,4) NOT NULL DEFAULT 0,

    -- Optional foreign currency
    currency_id            INTEGER REFERENCES public.currencies(id),
    exchange_rate          NUMERIC(15,4) DEFAULT 1,

    -- Status & Approval
    status                 VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
                           CHECK (status IN ('DRAFT', 'APPROVED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED')),

    approval_request_id    INTEGER,
    approved_by            VARCHAR(100),
    approved_at            TIMESTAMP WITHOUT TIME ZONE,

    -- Accounting
    from_voucher_id        INTEGER REFERENCES public.vouchers(id) ON DELETE SET NULL,
    to_voucher_id          INTEGER REFERENCES public.vouchers(id) ON DELETE SET NULL,

    -- Audit
    created_at             TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_transfer_number_tenant 
        UNIQUE (transfer_number, tenant_id),

    CONSTRAINT chk_warehouses_different 
        CHECK (from_warehouse_id != to_warehouse_id),

    CONSTRAINT chk_currency_logic 
        CHECK (
            (currency_id IS NULL AND exchange_rate = 1)
            OR (currency_id IS NOT NULL AND exchange_rate > 0)
        )
);

-- Indexes
CREATE INDEX idx_stock_transfer_tenant ON public.stock_transfers(tenant_id);
CREATE INDEX idx_stock_transfer_from ON public.stock_transfers(from_warehouse_id);
CREATE INDEX idx_stock_transfer_to ON public.stock_transfers(to_warehouse_id);
CREATE INDEX idx_stock_transfer_date ON public.stock_transfers(transfer_date);
CREATE INDEX idx_stock_transfer_status ON public.stock_transfers(status);

CREATE TABLE IF NOT EXISTS public.stock_transfer_items (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    transfer_id            INTEGER NOT NULL 
                           REFERENCES public.stock_transfers(id) ON DELETE CASCADE,

    line_no                INTEGER NOT NULL,

    product_id             INTEGER NOT NULL 
                           REFERENCES public.products(id) ON DELETE RESTRICT,

    batch_number           VARCHAR(50),

    -- Quantity
    quantity               NUMERIC(12,4) NOT NULL CHECK (quantity > 0),
    uom                    VARCHAR(20) NOT NULL DEFAULT 'NOS',

    -- Stock Before/After (for audit)
    from_stock_before      NUMERIC(12,4) NOT NULL DEFAULT 0,
    from_stock_after       NUMERIC(12,4) NOT NULL DEFAULT 0,
    to_stock_before        NUMERIC(12,4) NOT NULL DEFAULT 0,
    to_stock_after         NUMERIC(12,4) NOT NULL DEFAULT 0,

    -- Cost (from source warehouse)
    unit_cost_base         NUMERIC(15,4) NOT NULL CHECK (unit_cost_base >= 0),
    total_cost_base        NUMERIC(15,4) NOT NULL,

    -- Optional foreign currency
    currency_id            INTEGER REFERENCES public.currencies(id),
    unit_cost_foreign      NUMERIC(15,4),
    total_cost_foreign     NUMERIC(15,4),
    exchange_rate          NUMERIC(15,4) DEFAULT 1,

    -- Line reason
    reason                 VARCHAR(500),

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_transfer_item_line UNIQUE (transfer_id, line_no),

    CONSTRAINT chk_total_cost 
        CHECK (total_cost_base = ROUND(quantity * unit_cost_base, 4)),

    CONSTRAINT chk_foreign_cost 
        CHECK (
            total_cost_foreign IS NULL 
            OR total_cost_foreign = ROUND(quantity * unit_cost_foreign, 4)
        ),

    CONSTRAINT chk_currency_logic 
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
CREATE INDEX idx_transfer_items_transfer ON public.stock_transfer_items(transfer_id);
CREATE INDEX idx_transfer_items_product ON public.stock_transfer_items(product_id);