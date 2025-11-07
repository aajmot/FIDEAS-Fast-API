DROP TABLE IF EXISTS public.addresses;
CREATE TABLE IF NOT EXISTS public.addresses (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    -- Link to any entity (polymorphic)
    entity_type            VARCHAR(30) NOT NULL 
                           CHECK (entity_type IN (
                               'CUSTOMER', 'SUPPLIER', 'WAREHOUSE', 
                               'EMPLOYEE', 'BRANCH', 'OTHER'
                           )),

    entity_id              INTEGER NOT NULL,

    -- Address Type
    address_type           VARCHAR(20) NOT NULL DEFAULT 'BILLING'
                           CHECK (address_type IN ('BILLING', 'SHIPPING', 'WAREHOUSE', 'REGISTERED')),

    -- Core Address
    address_line1          VARCHAR(200) NOT NULL,
    address_line2          VARCHAR(200),
    city                   VARCHAR(100) NOT NULL,
    state                  VARCHAR(100) NOT NULL,
    country                VARCHAR(100) NOT NULL DEFAULT 'India',
    pincode                VARCHAR(20) NOT NULL,

    -- GST & Compliance
    gstin                  VARCHAR(15),                     -- 15-digit GSTIN
    state_code             VARCHAR(2),                      -- e.g. '27' for MH
    is_gst_registered      BOOLEAN DEFAULT FALSE,

    -- Contact
    contact_person         VARCHAR(100),
    phone                  VARCHAR(20),
    email                  VARCHAR(100),

    -- Default Flags
    is_default_billing     BOOLEAN DEFAULT FALSE,
    is_default_shipping    BOOLEAN DEFAULT FALSE,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_entity_address 
        UNIQUE (tenant_id, entity_type, entity_id, address_type, is_deleted)
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT chk_gstin_format 
        CHECK (
            gstin IS NULL 
            OR gstin ~ '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
        ),

    CONSTRAINT chk_pincode_india 
        CHECK (
            country != 'India' 
            OR pincode ~ '^[1-9][0-9]{5}$'
        ),

    CONSTRAINT chk_default_uniqueness 
        CHECK (
            NOT (is_default_billing AND is_default_shipping)
            OR (entity_type = 'CUSTOMER' OR entity_type = 'SUPPLIER')
        )
);

-- Indexes
CREATE INDEX idx_addresses_tenant ON public.addresses(tenant_id);
CREATE INDEX idx_addresses_entity ON public.addresses(entity_type, entity_id);
CREATE INDEX idx_addresses_gstin ON public.addresses(gstin);
CREATE INDEX idx_addresses_pincode ON public.addresses(pincode);
CREATE INDEX idx_addresses_default_billing 
    ON public.addresses(tenant_id, entity_type, entity_id) 
    WHERE is_default_billing = TRUE AND is_deleted = FALSE;
CREATE INDEX idx_addresses_default_shipping 
    ON public.addresses(tenant_id, entity_type, entity_id) 
    WHERE is_default_shipping = TRUE AND is_deleted = FALSE;