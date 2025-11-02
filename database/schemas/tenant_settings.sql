-- Table: public.tenant_settings
DROP TABLE IF EXISTS public.tenant_settings;

CREATE TABLE IF NOT EXISTS public.tenant_settings
(
    id SERIAL NOT NULL,
    tenant_id integer NOT NULL,
    setting text COLLATE pg_catalog."default" NOT NULL,
    description text COLLATE pg_catalog."default",
    value_type text COLLATE pg_catalog."default" DEFAULT 'BOOLEAN'::text,
    value text COLLATE pg_catalog."default" DEFAULT 'TRUE'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by text COLLATE pg_catalog."default",
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by text COLLATE pg_catalog."default",
    CONSTRAINT tenant_settings_pkey PRIMARY KEY (id),
    CONSTRAINT tenant_settings_tenant_id_setting_key UNIQUE (tenant_id, setting),
    CONSTRAINT tenant_settings_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT tenant_settings_value_type_check CHECK (value_type = ANY (ARRAY['TEXT'::text,'CURRENCY'::text, 'BOOLEAN'::text, 'INTEGER'::text]))
);

DROP INDEX IF EXISTS public.idx_tenant_settings_tenant_id;

CREATE INDEX IF NOT EXISTS idx_tenant_settings_tenant_id
    ON public.tenant_settings USING btree
    (tenant_id ASC NULLS LAST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;

