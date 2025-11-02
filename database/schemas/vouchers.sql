-- Table: public.vouchers

DROP TABLE IF EXISTS public.vouchers;

CREATE TABLE IF NOT EXISTS public.vouchers
(
    id SERIAL,
    tenant_id integer NOT NULL,
    voucher_number character varying(50) NOT NULL,
    voucher_type_id integer NOT NULL,
    voucher_date timestamp without time zone NOT NULL,
    reference_type character varying(20),
    reference_id integer,
    reference_number character varying(50),
    narration text,

    currency_amount numeric(15,4),
    currency_id integer,
    exchange_rate numeric(15,4) DEFAULT 1,
    total_amount numeric(15,4) NOT NULL,
    total_debit numeric(15,4) NOT NULL,
    total_credit numeric(15,4) NOT NULL,

    is_posted boolean DEFAULT true,
    reversed_voucher_id integer,
    reversal_voucher_id integer,
    is_reversal boolean DEFAULT false,
    approval_status character varying(20),
    approval_request_id integer,


    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by text DEFAULT 'system'::text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by text DEFAULT 'system'::text,
    is_deleted boolean DEFAULT false,

    CONSTRAINT vouchers_pkey PRIMARY KEY (id),
    CONSTRAINT vouchers_voucher_number_key UNIQUE (voucher_number),
    CONSTRAINT vouchers_currency_id_fkey FOREIGN KEY (currency_id)
        REFERENCES public.currencies (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT vouchers_reversal_voucher_id_fkey FOREIGN KEY (reversal_voucher_id)
        REFERENCES public.vouchers (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT vouchers_reversed_voucher_id_fkey FOREIGN KEY (reversed_voucher_id)
        REFERENCES public.vouchers (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT vouchers_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT vouchers_voucher_type_id_fkey FOREIGN KEY (voucher_type_id)
        REFERENCES public.voucher_types (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);



-- Table: public.voucher_details

DROP TABLE IF EXISTS public.voucher_details;

CREATE TABLE IF NOT EXISTS public.voucher_details
(
    id SERIAL,
    tenant_id integer NOT NULL,
    voucher_id integer NOT NULL,
    account_id integer NOT NULL,
    description text,
    debit_amount numeric(15,4),
    credit_amount numeric(15,4),

    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by text DEFAULT 'system'::text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by text DEFAULT 'system'::text,
    is_deleted boolean DEFAULT false,

    CONSTRAINT voucher_details_pkey PRIMARY KEY (id),
    CONSTRAINT voucher_details_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT voucher_details_voucher_id_fkey FOREIGN KEY (voucher_id)
        REFERENCES public.vouchers (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT voucher_details_account_id_fkey FOREIGN KEY (account_id)
        REFERENCES public.accounts (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);