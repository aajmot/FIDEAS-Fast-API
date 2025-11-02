-- Table: public.account_masters

DROP TABLE IF EXISTS public.account_masters;

CREATE TABLE IF NOT EXISTS public.account_masters
(
    id SERIAL,
    tenant_id integer NOT NULL,
    account_group_id integer NOT NULL,

    code character varying(50)  NOT NULL,
    name character varying(200)  NOT NULL,
    description text,

    
    opening_balance numeric(15,4),
    current_balance numeric(15,4),
    is_system_assigned boolean DEFAULT false,
    
    is_active boolean,
    
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by text DEFAULT 'system'::text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by text DEFAULT 'system'::text,
    is_deleted boolean DEFAULT false,


    CONSTRAINT account_masters_pkey PRIMARY KEY (id),
    CONSTRAINT uq_account_master_code_tenant UNIQUE (code, tenant_id),
    CONSTRAINT account_masters_account_group_id_fkey FOREIGN KEY (account_group_id)
        REFERENCES public.account_groups (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT account_masters_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);