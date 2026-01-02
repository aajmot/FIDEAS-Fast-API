DROP TABLE IF EXISTS public.branches;

CREATE TABLE IF NOT EXISTS public.branches (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    -- Branch Info
    branch_code            VARCHAR(50) NOT NULL,
    branch_name            VARCHAR(200) NOT NULL,
    branch_type            VARCHAR(20) DEFAULT 'BRANCH'
                           CHECK (branch_type IN ('HEAD_OFFICE','BRANCH','WAREHOUSE','LAB','CLINIC')),

    -- Contact
    phone                  VARCHAR(20),
    email                  VARCHAR(100),
    contact_person         VARCHAR(100),

    -- Address
    address_line1          VARCHAR(200),
    address_line2          VARCHAR(200),
    city                   VARCHAR(100),
    state                  VARCHAR(100),
    pincode                VARCHAR(20),
    country                VARCHAR(100) DEFAULT 'INDIA',

    -- Tax Registration
    gstin                  VARCHAR(20),
    pan                    VARCHAR(20),
    tan                    VARCHAR(20),

    -- Banking
    bank_account_id        INTEGER 
                           REFERENCES public.bank_accounts(id) ON DELETE SET NULL,

    -- Accounting
    cost_center_id         INTEGER,
    profit_center_id       INTEGER,

    -- Manager
    manager_id             INTEGER,
    manager_name           VARCHAR(100),

    -- Status
    is_default             BOOLEAN DEFAULT FALSE,
    status                 VARCHAR(20) DEFAULT 'ACTIVE'
                           CHECK (status IN ('ACTIVE','INACTIVE','CLOSED')),

    remarks                TEXT,
    tags                   TEXT[],

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_branch_code_tenant 
        UNIQUE (branch_code, tenant_id)
);

-- Indexes
CREATE INDEX idx_branches_tenant ON public.branches(tenant_id);
CREATE INDEX idx_branches_status ON public.branches(status);
CREATE INDEX idx_branches_branch_code ON public.branches(branch_code);
CREATE INDEX idx_branches_default ON public.branches(is_default) WHERE is_default = TRUE;
