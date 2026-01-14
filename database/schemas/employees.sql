DROP TABLE IF EXISTS public.employee_cost_allocations;
-- Department Table
DROP TABLE IF EXISTS public.employees;
-- Employee Table (for all employee types)
CREATE TABLE IF NOT EXISTS public.employees (
    id                     SERIAL PRIMARY KEY,
    tenant_id              INTEGER NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id              INTEGER REFERENCES public.branches(id) ON DELETE SET NULL,
	department_id          INTEGER REFERENCES public.departments(id) ON DELETE SET NULL,
    
    employee_code          VARCHAR(50) NOT NULL,
    employee_name          VARCHAR(200) NOT NULL,
    employee_type          VARCHAR(50) NOT NULL DEFAULT 'OTHERS' CHECK (employee_type IN ('LAB_TECHNICIAN','DOCTOR','NURSE','ADMIN','OTHERS')),
    
    phone                  VARCHAR(20),
    email                  VARCHAR(100),
    
    qualification          VARCHAR(100),
    specialization         VARCHAR(100),
    license_number         VARCHAR(50),
    license_expiry         DATE,
    
    employment_type        VARCHAR(20) DEFAULT 'INTERNAL' CHECK (employment_type IN ('INTERNAL','EXTERNAL','CONTRACT')),
    
    status                 VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE','SUSPENDED')),
    
    remarks                TEXT,
    
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    is_active              BOOLEAN DEFAULT TRUE,
    is_deleted             BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT uq_employee_code_tenant UNIQUE (employee_code, tenant_id)
);

-- Indexes
CREATE INDEX idx_departments_tenant ON public.departments(tenant_id);
CREATE INDEX idx_departments_status ON public.departments(status);

CREATE INDEX idx_employees_tenant ON public.employees(tenant_id);
CREATE INDEX idx_employees_department ON public.employees(department_id);
CREATE INDEX idx_employees_type ON public.employees(employee_type);
CREATE INDEX idx_employees_status ON public.employees(status);
CREATE INDEX idx_employees_code ON public.employees(employee_code);


CREATE TABLE employee_cost_allocations (
    id SERIAL PRIMARY KEY,
    tenant_id              INTEGER NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    branch_id              INTEGER REFERENCES public.branches(id) ON DELETE SET NULL,

    employee_id integer REFERENCES employees(id),
    cost_center_id integer REFERENCES cost_centers(id),
    percentage decimal(5,2), -- e.g., 60.00
    effective_start_date date,
    effective_end_date date,

    status                 VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE')),
    
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(100) DEFAULT 'system',
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by             VARCHAR(100) DEFAULT 'system',
    -- is_deleted             BOOLEAN DEFAULT FALSE,


    CONSTRAINT total_pct_check_employee_cost_allocations CHECK (percentage <= 100)
);