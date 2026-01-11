-- Appointment Invoice Header
DROP TABLE IF EXISTS public.appointment_invoice_items;
DROP TABLE IF EXISTS public.appointment_invoices;

CREATE TABLE IF NOT EXISTS public.appointment_invoices (
    id                      SERIAL PRIMARY KEY,
    
    tenant_id               INTEGER NOT NULL
                            REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id               INTEGER
                            REFERENCES public.branches(id) ON DELETE SET NULL,
    
    appointment_id          INTEGER NOT NULL
                            REFERENCES public.appointments(id) ON DELETE RESTRICT,
    
    -- Invoice Info
    invoice_number          VARCHAR(50) NOT NULL,
    invoice_date            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date                DATE,
    
    -- Patient Info (denormalized for invoice record)
    patient_id              INTEGER NOT NULL
                            REFERENCES public.patients(id) ON DELETE RESTRICT,
    patient_name            VARCHAR(100),
    patient_phone           VARCHAR(20),
    patient_email           VARCHAR(100),
    patient_address         TEXT,
    patient_dob             DATE,
    patient_gender          VARCHAR(10),
    
    -- Doctor Info (denormalized)
    doctor_id               INTEGER NOT NULL
                            REFERENCES public.doctors(id) ON DELETE RESTRICT,
    doctor_name             VARCHAR(100),
    doctor_phone            VARCHAR(20),
    doctor_email            VARCHAR(100),
    doctor_address          TEXT,
    doctor_license_number   VARCHAR(50),
    doctor_speciality       VARCHAR(100),
    
    -- Billing Summary
    subtotal_amount         NUMERIC(12,4) NOT NULL DEFAULT 0,
    items_total_discount_amount NUMERIC(12,4) DEFAULT 0,
    taxable_amount          NUMERIC(12,4) NOT NULL DEFAULT 0,

    cgst_amount             NUMERIC(12,4) DEFAULT 0,
    sgst_amount             NUMERIC(12,4) DEFAULT 0,
    igst_amount             NUMERIC(12,4) DEFAULT 0,
    cess_amount             NUMERIC(12,4) DEFAULT 0,
    
    total_tax_amount        NUMERIC(12,4) GENERATED ALWAYS AS 
                            (cgst_amount + sgst_amount + igst_amount + cess_amount) STORED,

    overall_disc_percentage NUMERIC(5,4) NOT NULL DEFAULT 0,
    overall_disc_amount     NUMERIC(12,4) NOT NULL DEFAULT 0,
    
    roundoff                NUMERIC(12,4) DEFAULT 0,
    final_amount            NUMERIC(12,4) NOT NULL,

    -- Payment Tracking
    paid_amount             NUMERIC(12,4) NOT NULL DEFAULT 0,
    balance_amount          NUMERIC(12,4) GENERATED ALWAYS AS 
                            (final_amount - paid_amount) STORED,

    -- Status
    payment_status          VARCHAR(20) DEFAULT 'UNPAID'
                            CHECK (payment_status IN ('UNPAID','PARTIAL','PAID','OVERPAID')),
    
    status                  VARCHAR(20) DEFAULT 'DRAFT'
                            CHECK (status IN ('DRAFT','POSTED','CANCELLED')),

    -- Accounting
    voucher_id              INTEGER 
                            REFERENCES public.vouchers(id) ON DELETE SET NULL,

    -- Notes
    notes                   TEXT,
    tags                    TEXT[],
    
    -- Audit
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by              VARCHAR(100) DEFAULT 'system',
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by              VARCHAR(100) DEFAULT 'system',
    is_active               BOOLEAN DEFAULT TRUE,
    is_deleted              BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT uq_invoice_number_tenant_appointment_invoices 
        UNIQUE (invoice_number, tenant_id),

    CONSTRAINT chk_invoice_amounts_appointment_invoices 
        CHECK (final_amount >= 0 AND paid_amount >= 0)
);

-- Appointment Invoice Line Items
CREATE TABLE IF NOT EXISTS public.appointment_invoice_items (
    id                      SERIAL PRIMARY KEY,

    tenant_id               INTEGER NOT NULL 
                            REFERENCES public.tenants(id) ON DELETE CASCADE,
    
    invoice_id              INTEGER NOT NULL
                            REFERENCES public.appointment_invoices(id) ON DELETE CASCADE,

    line_no                 INTEGER NOT NULL,
    
    -- Reference to billing master
    billing_master_id       INTEGER
                            REFERENCES public.clinic_billing_master(id) ON DELETE RESTRICT,
    
    -- Item details (denormalized for invoice record)
    description             TEXT NOT NULL,
    hsn_code                VARCHAR(20),
    
    -- Pricing
    quantity                INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price              NUMERIC(12,4) NOT NULL CHECK (unit_price >= 0),
    rate                    NUMERIC(12,4) NOT NULL,
    disc_percentage         NUMERIC(5,2) DEFAULT 0,
    disc_amount             NUMERIC(12,4) DEFAULT 0,
    
    taxable_amount          NUMERIC(12,4) NOT NULL,
    cgst_rate               NUMERIC(5,2) DEFAULT 0,
    cgst_amount             NUMERIC(12,4) DEFAULT 0,
    sgst_rate               NUMERIC(5,2) DEFAULT 0,
    sgst_amount             NUMERIC(12,4) DEFAULT 0,
    igst_rate               NUMERIC(5,2) DEFAULT 0,
    igst_amount             NUMERIC(12,4) DEFAULT 0,
    cess_rate               NUMERIC(5,2) DEFAULT 0,
    cess_amount             NUMERIC(12,4) DEFAULT 0,
    
    total_amount            NUMERIC(12,4) NOT NULL,

    remarks                 TEXT,
    
    -- Audit
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by              VARCHAR(100) DEFAULT 'system',
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by              VARCHAR(100) DEFAULT 'system',
    is_deleted              BOOLEAN DEFAULT FALSE,

    CONSTRAINT uq_appointment_invoice_item_line 
        UNIQUE (invoice_id, line_no),

    CONSTRAINT chk_appointment_invoice_item_amount 
        CHECK (total_amount >= 0)
);

-- Indexes for appointment_invoices
CREATE INDEX idx_appointment_invoices_tenant ON public.appointment_invoices(tenant_id);
CREATE INDEX idx_appointment_invoices_branch ON public.appointment_invoices(branch_id);
CREATE INDEX idx_appointment_invoices_appointment ON public.appointment_invoices(appointment_id);
CREATE INDEX idx_appointment_invoices_patient ON public.appointment_invoices(patient_id);
CREATE INDEX idx_appointment_invoices_doctor ON public.appointment_invoices(doctor_id);
CREATE INDEX idx_appointment_invoices_date ON public.appointment_invoices(invoice_date);
CREATE INDEX idx_appointment_invoices_payment_status ON public.appointment_invoices(payment_status);
CREATE INDEX idx_appointment_invoices_status ON public.appointment_invoices(status);

-- Indexes for appointment_invoice_items
CREATE INDEX idx_appointment_invoice_items_invoice ON public.appointment_invoice_items(invoice_id);
CREATE INDEX idx_appointment_invoice_items_billing_master ON public.appointment_invoice_items(billing_master_id);
