DROP TABLE IF EXISTS public.sample_collection_items;
DROP TABLE IF EXISTS public.sample_collections;

CREATE TABLE IF NOT EXISTS public.sample_collections (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,
    
    branch_id              INTEGER REFERENCES public.branches(id) ON DELETE SET NULL,

    -- Collection Info
    collection_number      VARCHAR(50) NOT NULL,
    collection_date        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Test Order
    test_order_id          INTEGER NOT NULL 
                           REFERENCES public.test_orders(id) ON DELETE RESTRICT,

    -- Patient
    patient_id             INTEGER NOT NULL 
                           REFERENCES public.patients(id) ON DELETE RESTRICT,
    patient_name           VARCHAR(200) NOT NULL,
    patient_phone          VARCHAR(20) NOT NULL,

    -- Referring Doctor (internal or external)  
    referring_doctor_id    INTEGER                     -- ADD: Internal doctor reference
                        REFERENCES public.doctors(id) ON DELETE SET NULL,
    referring_doctor_name  VARCHAR(100),               -- ADD: External doctor name
    referring_doctor_phone  VARCHAR(100),               -- ADD: External doctor phone
    referring_doctor_license VARCHAR(100),               -- ADD: External doctor license
    is_external_doctor     BOOLEAN DEFAULT FALSE,      -- ADD: Flag for external doctor

    -- Collector
    collector_id           INTEGER 
                           REFERENCES public.employees(id) ON DELETE SET NULL,
    collector_name         VARCHAR(100),
    collector_phone        VARCHAR(20),
    is_external_collector  BOOLEAN DEFAULT FALSE,

    -- Lab Technician (internal or external)
    lab_technician_id      INTEGER 
                           REFERENCES public.employees(id) ON DELETE SET NULL,
    lab_technician_name    VARCHAR(100),
    lab_technician_phone   VARCHAR(20),
    lab_technician_email   VARCHAR(100),
    is_external_technician BOOLEAN DEFAULT FALSE,
    received_at            TIMESTAMP,

    -- Sample Type
    sample_type            VARCHAR(50) NOT NULL 
                           CHECK (sample_type IN ('BLOOD','URINE','STOOL','SPUTUM','SWAB','TISSUE','OTHER')),

    -- Collection Details
    collection_method      VARCHAR(50),
    collection_site        VARCHAR(100),
    container_type         VARCHAR(50),
    sample_volume          NUMERIC(10,2),
    volume_unit            VARCHAR(20) DEFAULT 'ml',

    -- Condition
    sample_condition       VARCHAR(50) DEFAULT 'NORMAL'
                           CHECK (sample_condition IN ('NORMAL','HEMOLYZED','CLOTTED','INSUFFICIENT','CONTAMINATED','REJECTED')),

    -- Fasting
    is_fasting             BOOLEAN DEFAULT FALSE,
    fasting_hours          INTEGER,

    -- Status
    status                 VARCHAR(20) DEFAULT 'COLLECTED'
                           CHECK (status IN ('COLLECTED','RECEIVED','PROCESSING','COMPLETED','REJECTED')),


    -- Rejection
    rejection_reason       TEXT,
    rejected_at            TIMESTAMP,

    remarks                TEXT,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_collection_number_tenant 
        UNIQUE (collection_number, tenant_id)
);

-- Indexes
CREATE INDEX idx_sample_collections_tenant ON public.sample_collections(tenant_id);
CREATE INDEX idx_sample_collections_test_order ON public.sample_collections(test_order_id);
CREATE INDEX idx_sample_collections_patient ON public.sample_collections(patient_id);
CREATE INDEX idx_sample_collections_status ON public.sample_collections(status);
CREATE INDEX idx_sample_collections_date ON public.sample_collections(collection_date);


CREATE TABLE IF NOT EXISTS public.sample_collection_items (
    id                     SERIAL PRIMARY KEY,

    tenant_id              INTEGER NOT NULL 
                           REFERENCES public.tenants(id) ON DELETE CASCADE,

    collection_id          INTEGER NOT NULL 
                           REFERENCES public.sample_collections(id) ON DELETE CASCADE,

    line_no                INTEGER NOT NULL,

    -- Test Order Item
    test_order_item_id     INTEGER NOT NULL 
                           REFERENCES public.test_order_items(id) ON DELETE RESTRICT,

    -- Test Info
    test_id                INTEGER 
                           REFERENCES public.tests(id) ON DELETE RESTRICT,
    test_name              VARCHAR(200),

    -- Sample Requirement
    required_volume        NUMERIC(10,2),
    collected_volume       NUMERIC(10,2),

    -- Status
    item_status            VARCHAR(20) DEFAULT 'COLLECTED'
                           CHECK (item_status IN ('COLLECTED','RECEIVED','IN_PROGRESS','COMPLETED','REJECTED')),

    -- Results
    result_value           TEXT,
    result_unit            VARCHAR(50),
    reference_range        VARCHAR(100),
    is_abnormal            BOOLEAN DEFAULT FALSE,

    -- Timing
    started_at             TIMESTAMP,
    completed_at           TIMESTAMP,
    verified_at            TIMESTAMP,
    verified_by            VARCHAR(100),

    remarks                TEXT,

    -- Audit
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT uq_collection_item_line 
        UNIQUE (collection_id, line_no)
);

-- Indexes
CREATE INDEX idx_sample_collection_items_collection ON public.sample_collection_items(collection_id);
CREATE INDEX idx_sample_collection_items_test_order_item ON public.sample_collection_items(test_order_item_id);
CREATE INDEX idx_sample_collection_items_test ON public.sample_collection_items(test_id);
CREATE INDEX idx_sample_collection_items_status ON public.sample_collection_items(item_status);
