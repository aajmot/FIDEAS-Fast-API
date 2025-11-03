-- Table: public.transaction_templates

DROP TABLE IF EXISTS public.transaction_templates_rules;
DROP TABLE IF EXISTS public.transaction_templates;

CREATE TABLE IF NOT EXISTS public.transaction_templates
(
    id SERIAL NOT NULL,
    tenant_id integer NOT NULL,

    module_id integer NOT NULL,
    transaction_type character varying(50)  NOT NULL,

    code character varying(20)  NOT NULL,
    name character varying(100)  NOT NULL,
    description character varying(255),


    
    
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(100) ,
    updated_at timestamp without time zone,
    updated_by character varying(100) ,

    CONSTRAINT transaction_templates_pkey PRIMARY KEY (id),
    CONSTRAINT transaction_templates_code_tenant_id_key UNIQUE (code, tenant_id),
    CONSTRAINT transaction_templates_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT transaction_templates_module_id_fkey FOREIGN KEY (module_id)
        REFERENCES public.module_master (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);


-- Table: public.transaction_template_rules

CREATE TABLE IF NOT EXISTS public.transaction_template_rules
(
    id SERIAL NOT NULL,
    tenant_id integer NOT NULL,
    template_id integer NOT NULL,
    
    line_number integer NOT NULL,
    account_type character varying(50) NOT NULL, -- ASSET/LIABILITY/INCOME/EXPENSE
    account_id integer NOT NULL,

    entry_type character varying(10)  NOT NULL, -- DEBIT/CREDIT
    amount_source character varying(50)  NOT NULL, --entity.total_amount, entity.tax_amount, fixed_amount

    narration text,
    is_sub_ledger boolean DEFAULT false,

    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(100) ,
    updated_at timestamp without time zone,
    updated_by character varying(100) ,
    is_deleted boolean DEFAULT false,


    CONSTRAINT transaction_template_rules_pkey PRIMARY KEY (id),
    CONSTRAINT transaction_template_rules_template_id_line_number_key UNIQUE (template_id, line_number),
    CONSTRAINT transaction_template_rules_account_id_fkey FOREIGN KEY (account_id)
        REFERENCES public.account_masters (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT transaction_template_rules_template_id_fkey FOREIGN KEY (template_id)
        REFERENCES public.transaction_templates (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT transaction_template_rules_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);
