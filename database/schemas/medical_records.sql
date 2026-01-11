DROP TABLE IF EXISTS public.medical_records;

CREATE TABLE IF NOT EXISTS public.medical_records (
    id                  SERIAL PRIMARY KEY,
    
    tenant_id           INTEGER NOT NULL
                        REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id           INTEGER
                        REFERENCES public.branches(id) ON DELETE SET NULL,
    
    appointment_id      INTEGER NOT NULL
                        REFERENCES public.appointments(id) ON DELETE RESTRICT,
    
    -- Record Info
    record_number       VARCHAR(50) NOT NULL,
    visit_date          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Patient & Doctor (denormalized)
    patient_id          INTEGER NOT NULL
                        REFERENCES public.patients(id) ON DELETE RESTRICT,
    patient_name        VARCHAR(100),
    
    doctor_id           INTEGER NOT NULL
                        REFERENCES public.doctors(id) ON DELETE RESTRICT,
    doctor_name         VARCHAR(100),
    
    -- Medical Details
    chief_complaint     TEXT,
    diagnosis           TEXT,
    treatment_plan      TEXT,
    vital_signs         TEXT,
    lab_results         TEXT,
    notes               TEXT,
    
    -- Audit
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(100) DEFAULT 'system',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by          VARCHAR(100) DEFAULT 'system',
    is_active           BOOLEAN DEFAULT TRUE,
    is_deleted          BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT uq_record_number_tenant 
        UNIQUE (record_number, tenant_id)
);

-- Indexes
CREATE INDEX idx_medical_records_tenant ON public.medical_records(tenant_id);
CREATE INDEX idx_medical_records_branch ON public.medical_records(branch_id);
CREATE INDEX idx_medical_records_appointment ON public.medical_records(appointment_id);
CREATE INDEX idx_medical_records_patient ON public.medical_records(patient_id);
CREATE INDEX idx_medical_records_doctor ON public.medical_records(doctor_id);
CREATE INDEX idx_medical_records_visit_date ON public.medical_records(visit_date);
