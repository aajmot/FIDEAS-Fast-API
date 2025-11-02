-- Table: public.account_groups

DROP TABLE IF EXISTS public.account_groups;

CREATE TABLE IF NOT EXISTS public.account_groups
(
    id SERIAL NOT NULL,
    tenant_id integer NOT NULL,

    account_type character varying(20)  NOT NULL, -- ASSET, LIABILITY, EQUITY, INCOME, EXPENSE
    name character varying(100)  NOT NULL,
    code character varying(20)  NOT NULL,
    parent_id integer,
    is_system_assigned boolean DEFAULT false,
    
    is_active boolean DEFAULT true,
    
    created_at timestamp without time zone,
    created_by character varying(100)  DEFAULT 'system'::character varying,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by character varying(100)  DEFAULT 'system'::character varying,
    is_deleted boolean DEFAULT false,
    
    CONSTRAINT account_groups_pkey PRIMARY KEY (id),
    CONSTRAINT uq_account_group_code_tenant UNIQUE (code, tenant_id),
    CONSTRAINT account_groups_parent_id_fkey FOREIGN KEY (parent_id)
        REFERENCES public.account_groups (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT account_groups_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

