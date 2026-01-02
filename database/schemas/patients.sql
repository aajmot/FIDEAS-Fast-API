DROP TABLE IF EXISTS public.patients;

CREATE TABLE IF NOT EXISTS public.patients (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    -- Patient Info
    patient_number         VARCHAR(50) NOT NULL,
    first_name             VARCHAR(100) NOT NULL,
    last_name              VARCHAR(100) NOT NULL,
    full_name              VARCHAR(200) GENERATED ALWAYS AS 
                           (first_name || ' ' || last_name) STORED,

    -- Demographics
    date_of_birth          DATE,
    age                    INTEGER GENERATED ALWAYS AS 
                           (EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth))::INTEGER) STORED,
    gender                 VARCHAR(10) 
                           CHECK (gender IN ('MALE','FEMALE','OTHER')),
    blood_group            VARCHAR(5) 
                           CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),

    -- Contact
    phone                  VARCHAR(20) NOT NULL,
    email                  VARCHAR(100),
    alternate_phone        VARCHAR(20),
    address                TEXT,

    -- Emergency Contact
    emergency_contact      VARCHAR(100),
    emergency_phone        VARCHAR(20),
    emergency_relation     VARCHAR(50),

    -- Medical Info
    allergies              TEXT,
    chronic_conditions     TEXT[],
    current_medications    TEXT,
    medical_history        TEXT,

    -- Insurance
    insurance_provider     VARCHAR(100),
    insurance_number       VARCHAR(50),
    insurance_expiry       DATE,

    -- Identification
    id_proof_type          VARCHAR(50),
    id_proof_number        VARCHAR(50),

    -- Status
    status                 VARCHAR(20) DEFAULT 'ACTIVE'
                           CHECK (status IN ('ACTIVE','INACTIVE','DECEASED','TRANSFERRED')),

    -- Remarks
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
    CONSTRAINT uq_patient_number_tenant 
        UNIQUE (patient_number, tenant_id)
);

-- Indexes
CREATE INDEX idx_patients_tenant ON public.patients(tenant_id);
CREATE INDEX idx_patients_status ON public.patients(status);
CREATE INDEX idx_patients_phone ON public.patients(phone);
CREATE INDEX idx_patients_dob ON public.patients(date_of_birth);
CREATE INDEX idx_patients_patient_number ON public.patients(patient_number);
