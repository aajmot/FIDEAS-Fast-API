DROP TABLE IF EXISTS public.doctors;

CREATE TABLE IF NOT EXISTS public.doctors (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    -- Employee Info
    employee_id            VARCHAR(50) NOT NULL,
    first_name             VARCHAR(100) NOT NULL,
    last_name              VARCHAR(100) NOT NULL,
    full_name              VARCHAR(200) GENERATED ALWAYS AS 
                           (first_name || ' ' || last_name) STORED,

    -- Professional Info
    specialization         VARCHAR(100),
    license_number         VARCHAR(50),
    qualification          VARCHAR(200),
    experience_years       INTEGER,

    -- Contact
    phone                  VARCHAR(20) NOT NULL,
    email                  VARCHAR(100),
    alternate_phone        VARCHAR(20),

    -- Schedule
    schedule_start         TIME,
    schedule_end           TIME,
    working_days           TEXT[],  -- ['MON','TUE','WED']
    consultation_duration  INTEGER DEFAULT 15,  -- minutes

    -- Fees
    consultation_fee       NUMERIC(12,4) DEFAULT 0,
    followup_fee           NUMERIC(12,4) DEFAULT 0,
    emergency_fee          NUMERIC(12,4) DEFAULT 0,

    -- Commission
    commission_type        VARCHAR(20) DEFAULT 'PERCENTAGE'
                           CHECK (commission_type IN ('FIXED','PERCENTAGE')),
    commission_value       NUMERIC(10,2) DEFAULT 0,

    -- Department
    department_id          INTEGER,
    department_name        VARCHAR(100),

    -- Status
    status                 VARCHAR(20) DEFAULT 'ACTIVE'
                           CHECK (status IN ('ACTIVE','INACTIVE','ON_LEAVE','RESIGNED')),

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
    CONSTRAINT uq_employee_id_tenant 
        UNIQUE (employee_id, tenant_id),

    CONSTRAINT chk_schedule_time 
        CHECK (schedule_start IS NULL OR schedule_end IS NULL OR schedule_end > schedule_start),

    CONSTRAINT chk_positive_fees 
        CHECK (consultation_fee >= 0 AND followup_fee >= 0 AND emergency_fee >= 0)
);

-- Indexes
CREATE INDEX idx_doctors_tenant ON public.doctors(tenant_id);
CREATE INDEX idx_doctors_status ON public.doctors(status);
CREATE INDEX idx_doctors_specialization ON public.doctors(specialization);
CREATE INDEX idx_doctors_employee_id ON public.doctors(employee_id);
