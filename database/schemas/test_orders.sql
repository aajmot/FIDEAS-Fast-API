DROP TABLE IF EXISTS public.test_order_items;
DROP TABLE IF EXISTS public.test_orders;

CREATE TABLE IF NOT EXISTS public.test_orders (
    id                     SERIAL PRIMARY KEY,
    
    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    -- Order Info
    test_order_number      VARCHAR(50) NOT NULL,
    order_date             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Patient
    patient_id             INTEGER 
                           REFERENCES public.patients(id) ON DELETE SET NULL,
    patient_name           VARCHAR(200) NOT NULL,
    patient_phone          VARCHAR(20) NOT NULL,

    -- Doctor
    doctor_id              INTEGER 
                           REFERENCES public.doctors(id) ON DELETE SET NULL,
    doctor_name            VARCHAR(200) NOT NULL,
    doctor_phone           VARCHAR(20),
    doctor_license_number  VARCHAR(100),

    -- Appointment
    appointment_id         INTEGER 
                           REFERENCES public.appointments(id) ON DELETE SET NULL,

    -- Agency/Referral
    agency_id              INTEGER 
                           REFERENCES public.agencies(id) ON DELETE SET NULL,

    -- Amounts
    subtotal_amount        NUMERIC(12,4) NOT NULL DEFAULT 0,
    items_total_discount_amount NUMERIC(12,4) DEFAULT 0,  -- Sum of all item discounts

    taxable_amount         NUMERIC(12,4) NOT NULL DEFAULT 0,

    cgst_amount            NUMERIC(12,4) DEFAULT 0,
    sgst_amount            NUMERIC(12,4) DEFAULT 0,
    igst_amount            NUMERIC(12,4) DEFAULT 0,
    cess_amount            NUMERIC(12,4) DEFAULT 0,
    
    total_tax_amount       NUMERIC(12,4) GENERATED ALWAYS AS 
                           (cgst_amount + sgst_amount + igst_amount + cess_amount) STORED,

    overall_disc_percentage        NUMERIC(5,4) NOT NULL DEFAULT 0,
    overall_disc_amount            NUMERIC(12,4) NOT NULL DEFAULT 0,
    overall_cess_percentage        NUMERIC(5,4) NOT NULL DEFAULT 0,
    overall_cess_amount            NUMERIC(12,4) NOT NULL DEFAULT 0,

    roundoff               NUMERIC(12,4) DEFAULT 0,
    final_amount           NUMERIC(12,4) NOT NULL,

    -- Priority
    urgency                VARCHAR(20) DEFAULT 'ROUTINE'
                           CHECK (urgency IN ('ROUTINE','URGENT','STAT','CRITICAL')),

    -- Status
    status                 VARCHAR(20) DEFAULT 'DRAFT'
                           CHECK (status IN ('DRAFT','ORDERED','SAMPLE_COLLECTED','IN_PROGRESS','COMPLETED','CANCELLED','REPORTED')),

    -- Notes
    notes                  TEXT,
    tags                   TEXT[],
    barcode_data            VARCHAR(100) GENERATED ALWAYS AS (test_order_number) STORED,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_test_order_number_tenant 
        UNIQUE (test_order_number, tenant_id),

    CONSTRAINT chk_positive_amounts 
        CHECK (final_amount >= 0)
);

-- Indexes
CREATE INDEX idx_test_orders_tenant ON public.test_orders(tenant_id);
CREATE INDEX idx_test_orders_patient ON public.test_orders(patient_id);
CREATE INDEX idx_test_orders_doctor ON public.test_orders(doctor_id);
CREATE INDEX idx_test_orders_appointment ON public.test_orders(appointment_id);
CREATE INDEX idx_test_orders_status ON public.test_orders(status);
CREATE INDEX idx_test_orders_date ON public.test_orders(order_date);


CREATE TABLE IF NOT EXISTS public.test_order_items (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    test_order_id          INTEGER NOT NULL 
                           REFERENCES public.test_orders(id) ON DELETE CASCADE,

    line_no                INTEGER NOT NULL,

    -- Test or Panel
    test_id                INTEGER 
                           REFERENCES public.tests(id) ON DELETE RESTRICT,
    test_name              VARCHAR(200),
    
    panel_id               INTEGER 
                           REFERENCES public.test_panels(id) ON DELETE RESTRICT,
    panel_name             VARCHAR(200),

    -- Pricing
    rate                   NUMERIC(12,4) NOT NULL,
    disc_percentage        NUMERIC(5,2) DEFAULT 0,
    disc_amount            NUMERIC(12,4) DEFAULT 0,
    
    taxable_amount         NUMERIC(12,4) NOT NULL,
    cgst_rate              NUMERIC(5,2) DEFAULT 0,
    cgst_amount            NUMERIC(12,4) DEFAULT 0,
    sgst_rate              NUMERIC(5,2) DEFAULT 0,
    sgst_amount            NUMERIC(12,4) DEFAULT 0,
    igst_rate              NUMERIC(5,2) DEFAULT 0,
    igst_amount            NUMERIC(12,4) DEFAULT 0,
    cess_rate              NUMERIC(5,2) DEFAULT 0,
    cess_amount            NUMERIC(12,4) DEFAULT 0,
    
    total_amount           NUMERIC(12,4) NOT NULL,

    -- Status
    item_status            VARCHAR(20) DEFAULT 'PENDING'
                           CHECK (item_status IN ('PENDING','SAMPLE_COLLECTED','IN_PROGRESS','COMPLETED','CANCELLED')),

    remarks                TEXT,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_test_order_item_line 
        UNIQUE (test_order_id, line_no),

    -- CONSTRAINT chk_test_or_panel 
    --     CHECK ((test_id IS NOT NULL AND panel_id IS NULL) OR (test_id IS NULL AND panel_id IS NOT NULL)),

    CONSTRAINT chk_item_amount_positive 
        CHECK (total_amount >= 0)
);

-- Indexes
CREATE INDEX idx_test_order_items_order ON public.test_order_items(test_order_id);
CREATE INDEX idx_test_order_items_test ON public.test_order_items(test_id);
CREATE INDEX idx_test_order_items_panel ON public.test_order_items(panel_id);
CREATE INDEX idx_test_order_items_status ON public.test_order_items(item_status);
