DROP TABLE IF EXISTS public.cost_centers;
CREATE TABLE IF NOT EXISTS public.cost_centers (
    id SERIAL PRIMARY KEY,
    tenant_id integer NOT NULL 
        REFERENCES public.tenants(id) ON DELETE CASCADE,
    legal_entity_id integer -- Links to the Legal Entity
         REFERENCES public.legal_entities(id) ON DELETE CASCADE,
    code varchar(20) NOT NULL,
    name varchar(100) NOT NULL,
    description text,
    
    -- Hierarchy & Type
    parent_id integer,
    category varchar(20) DEFAULT 'NA' CHECK (category IN ('PRODUCTION','MARKETING','ADMIN','NA')), -- e.g., Production, Marketing, Admin
    
    -- Responsibility
    manager_id integer -- Links to Employees table
        REFERENCES public.employees(id) ON DELETE SET NULL,
    department_id integer -- Links to the HR Org structure/linked to 
        REFERENCES public.departments(id) ON DELETE SET NULL,
    
    -- Temporal Data (Effective Dating)
    valid_from date NOT NULL DEFAULT CURRENT_DATE,
    valid_until date, -- NULL means active indefinitely
    
    -- Financial Controls
    is_active boolean DEFAULT true,
    lock_posting boolean DEFAULT false, -- Stop expenses from hitting this CC
    currency_code char(3), -- If different from Company currency
    
    -- Audit Trail
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP,
    created_by integer,

    --CONSTRAINT uq_cc_code_tenant_legal_entity UNIQUE (code, tenant_id, legal_entity_id),
    CONSTRAINT fk_cc_parent FOREIGN KEY (parent_id) REFERENCES public.cost_centers (id)
);