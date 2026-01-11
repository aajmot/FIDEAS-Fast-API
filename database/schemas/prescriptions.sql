-- Prescriptions Header
DROP TABLE IF EXISTS public.prescription_test_items;
DROP TABLE IF EXISTS public.prescription_items;
DROP TABLE IF EXISTS public.prescriptions;

CREATE TABLE IF NOT EXISTS public.prescriptions (
    id                      SERIAL PRIMARY KEY,
    
    tenant_id               INTEGER NOT NULL
                            REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id               INTEGER
                            REFERENCES public.branches(id) ON DELETE SET NULL,
    
    appointment_id          INTEGER NOT NULL
                            REFERENCES public.appointments(id) ON DELETE RESTRICT,
    
    -- Prescription Info
    prescription_number     VARCHAR(50) NOT NULL,
    prescription_date       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Patient Info (denormalized)
    patient_id              INTEGER NOT NULL
                            REFERENCES public.patients(id) ON DELETE RESTRICT,
    patient_name            VARCHAR(100),
    patient_phone           VARCHAR(20),
    
    -- Doctor Info (denormalized)
    doctor_id               INTEGER NOT NULL
                            REFERENCES public.doctors(id) ON DELETE RESTRICT,
    doctor_name             VARCHAR(100),
    doctor_license_number   VARCHAR(50),
    
    instructions            TEXT,
    notes                   TEXT,
    
    -- Audit
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by              VARCHAR(100) DEFAULT 'system',
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by              VARCHAR(100) DEFAULT 'system',
    is_active               BOOLEAN DEFAULT TRUE,
    is_deleted              BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT uq_prescription_number_tenant 
        UNIQUE (prescription_number, tenant_id)
);

-- Prescription Medicine/Product Items
CREATE TABLE IF NOT EXISTS public.prescription_items (
    id                  SERIAL PRIMARY KEY,

    tenant_id               INTEGER NOT NULL
                            REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id               INTEGER
                            REFERENCES public.branches(id) ON DELETE SET NULL,
    
    prescription_id     INTEGER NOT NULL
                        REFERENCES public.prescriptions(id) ON DELETE CASCADE,
    
    product_id          INTEGER NOT NULL
                        REFERENCES public.products(id) ON DELETE RESTRICT,
    
    -- Product details (denormalized)
    product_name        VARCHAR(200),
    
    -- Dosage Instructions
    dosage              VARCHAR(100),
    frequency           VARCHAR(100),
    duration            VARCHAR(100),
    quantity            NUMERIC(10,2),
    instructions        TEXT,
    
    -- Audit
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_active           BOOLEAN DEFAULT TRUE,
    is_deleted          BOOLEAN DEFAULT FALSE
);

-- Prescription Test Items
CREATE TABLE IF NOT EXISTS public.prescription_test_items (
    id                  SERIAL PRIMARY KEY,
    
    tenant_id               INTEGER NOT NULL
                            REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id               INTEGER
                            REFERENCES public.branches(id) ON DELETE SET NULL,

    prescription_id     INTEGER NOT NULL
                        REFERENCES public.prescriptions(id) ON DELETE CASCADE,
    
    test_id             INTEGER NOT NULL
                        REFERENCES public.tests(id) ON DELETE RESTRICT,
    
    -- Test details (denormalized)
    test_name           VARCHAR(200),
    instructions        TEXT,
    
    -- Audit
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_active           BOOLEAN DEFAULT TRUE,
    is_deleted          BOOLEAN DEFAULT FALSE
);

-- Indexes for prescriptions
CREATE INDEX idx_prescriptions_tenant ON public.prescriptions(tenant_id);
CREATE INDEX idx_prescriptions_branch ON public.prescriptions(branch_id);
CREATE INDEX idx_prescriptions_appointment ON public.prescriptions(appointment_id);
CREATE INDEX idx_prescriptions_patient ON public.prescriptions(patient_id);
CREATE INDEX idx_prescriptions_doctor ON public.prescriptions(doctor_id);
CREATE INDEX idx_prescriptions_date ON public.prescriptions(prescription_date);

-- Indexes for prescription_items
CREATE INDEX idx_prescription_items_prescription ON public.prescription_items(prescription_id);
CREATE INDEX idx_prescription_items_product ON public.prescription_items(product_id);

-- Indexes for prescription_test_items
CREATE INDEX idx_prescription_test_items_prescription ON public.prescription_test_items(prescription_id);
CREATE INDEX idx_prescription_test_items_test ON public.prescription_test_items(test_id);
