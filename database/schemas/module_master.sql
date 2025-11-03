-- Table: public.module_master
DROP TABLE IF EXISTS public.module_master;

CREATE TABLE IF NOT EXISTS public.module_master
(
    id SERIAL NOT NULL,
    module_name character varying(100) NOT NULL,
    module_code character varying(50) NOT NULL,
    description text,
    is_mandatory boolean DEFAULT false,
    
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(100) DEFAULT 'system'::character varying,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by character varying(100) DEFAULT 'system'::character varying,
    is_deleted boolean DEFAULT false,
    
    CONSTRAINT module_master_pkey PRIMARY KEY (id),
    CONSTRAINT module_master_module_code_key UNIQUE (module_code),
    CONSTRAINT module_master_module_name_key UNIQUE (module_name)
);

