drop table if exists hsn_codes;
CREATE TABLE hsn_codes (
    id SERIAL,
    tenant_id integer NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    cgst_rate NUMERIC(5,2) DEFAULT 0,
    sgst_rate NUMERIC(5,2) DEFAULT 0,
    igst_rate NUMERIC(5,2) DEFAULT 0,
    cess_rate NUMERIC(5,2) DEFAULT 0,
    effective_from DATE,
    effective_to DATE,


    is_active boolean,
    created_at timestamp without time zone,
    created_by character varying(100) ,
    updated_by character varying(100) ,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted boolean DEFAULT false,

    CONSTRAINT hsn_codes_pkey PRIMARY KEY (id),
    CONSTRAINT hsn_codes_code_tenant_id_ukey UNIQUE (code, tenant_id),
    CONSTRAINT hsn_codes_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION

);