-- DROP TABLE IF EXISTS public.suppliers;

CREATE TABLE IF NOT EXISTS public.suppliers
(
    id SERIAL NOT NULL,
    tenant_id integer NOT NULL,
    name character varying(200) NOT NULL,
    phone character varying(20) NOT NULL,
    email character varying(100),
    tax_id character varying(50),
    address text,
    contact_person character varying(100),


    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(100) DEFAULT 'system'::character varying,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by character varying(100) DEFAULT 'system'::character varying,
    is_deleted boolean DEFAULT false,

    CONSTRAINT suppliers_pkey PRIMARY KEY (id),
    CONSTRAINT suppliers_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);
