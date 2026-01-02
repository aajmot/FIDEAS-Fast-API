DROP TABLE IF EXISTS public.departments CASCADE;

CREATE TABLE IF NOT EXISTS public.departments (
    id                     SERIAL PRIMARY KEY,
    tenant_id              INTEGER NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id              INTEGER REFERENCES public.branches(id) ON DELETE SET NULL,
    
    department_code        VARCHAR(50) NOT NULL,
    department_name        VARCHAR(200) NOT NULL,
    description            TEXT,
    
    status                 VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE')),
    
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_deleted             BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT uq_department_code_tenant UNIQUE (department_code, tenant_id)
);
