DROP TABLE IF EXISTS public.appointments;

CREATE TABLE IF NOT EXISTS public.appointments (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id              INTEGER
                           REFERENCES public.branches(id) ON DELETE SET NULL,

    -- Appointment Info
    appointment_number     VARCHAR(50) NOT NULL,
    appointment_date       DATE NOT NULL,
    appointment_time       TIME NOT NULL,
    duration_minutes       INTEGER,

    -- Parties
    patient_id             INTEGER NOT NULL 
                           REFERENCES public.patients(id) ON DELETE RESTRICT,
    patient_name           VARCHAR(100),
    patient_phone          VARCHAR(20),


    doctor_id              INTEGER NOT NULL 
                           REFERENCES public.doctors(id) ON DELETE RESTRICT,
    doctor_name            VARCHAR(100),
    doctor_phone           VARCHAR(20),
    doctor_license_number  VARCHAR(50),
    doctor_specialization  VARCHAR(100),

    -- Agency/Referral
    agency_id              INTEGER 
                           REFERENCES public.agencies(id) ON DELETE SET NULL,
    agency_name            VARCHAR(100),
    agency_phone           VARCHAR(20),

    -- Status
    status                 VARCHAR(20) DEFAULT 'SCHEDULED'
                           CHECK (status IN ('SCHEDULED','CONFIRMED','CANCELLED','COMPLETED','NO_SHOW')),

    -- Details
    reason                 TEXT,
    notes                  TEXT,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_appointment_number_tenant 
        UNIQUE (appointment_number, tenant_id)
);

-- Indexes
CREATE INDEX idx_appointments_tenant ON public.appointments(tenant_id);
CREATE INDEX idx_appointments_branch ON public.appointments(branch_id);
CREATE INDEX idx_appointments_patient ON public.appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON public.appointments(doctor_id);
CREATE INDEX idx_appointments_agency ON public.appointments(agency_id);
CREATE INDEX idx_appointments_date ON public.appointments(appointment_date);
CREATE INDEX idx_appointments_status ON public.appointments(status);
