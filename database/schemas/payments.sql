-- Table: public.payments

DROP TABLE IF EXISTS public.payments;

CREATE TABLE IF NOT EXISTS public.payments
(
    id SERIAL,
    tenant_id integer NOT NULL,

    payment_number character varying(50) NOT NULL,
    payment_date timestamp without time zone NOT NULL,
    payment_type character varying(20) NOT NULL,--'RECEIPT','PAYMENT','CONTRA'
    reference_voucher_id integer NOT NULL,
    part_type character varying(20) NOT NULL, --'CUSTOMER','SUPPLIER','EMPLOYEE','OTHER'
    part_id integer,
    total_amount numeric(15,2) NOT NULL,

    remarks text,
    status text DEFAULT 'POSTED', --'POSTED','CANCELLED','DRAFT'


    created_at timestamp without time zone,
    created_by character varying(100) DEFAULT 'system'::character varying,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by character varying(100) DEFAULT 'system'::character varying,
    is_deleted boolean DEFAULT false,

    CONSTRAINT payments_pkey PRIMARY KEY (id),
    CONSTRAINT payments_payment_number_key UNIQUE (payment_number),
    CONSTRAINT payments_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);


-- Table: public.payment_details    

DROP TABLE IF EXISTS public.payment_details;

CREATE TABLE IF NOT EXISTS public.payment_details
(
    id SERIAL,
    tenant_id integer NOT NULL,
    payment_id integer NOT NULL,
    payment_mode text NOT NULL, --'CASH','CHEQUE','ONLINE','CARD'
    instrument_number text,
    instrument_date timestamp without time zone,
    bank_name text,
    branch_name text,
    ifsc_code text,
    transaction_reference text,-- UPI Ref, Transaction ID
    amount numeric(15,4) NOT NULL,
    paid_from_account_id integer,-- e.g. Bank A/c, Cash A/c

    payment_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    account_id integer NOT NULL,
    description text,
    debit_amount numeric(15,4),
    credit_amount numeric(15,4),

    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by text DEFAULT 'system'::text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by text DEFAULT 'system'::text,
    is_deleted boolean DEFAULT false,

    CONSTRAINT payment_details_pkey PRIMARY KEY (id),
    CONSTRAINT payment_details_payment_id_fkey FOREIGN KEY (payment_id)
        REFERENCES public.payments (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT payment_details_account_id_fkey FOREIGN KEY (paid_from_account_id)
        REFERENCES public.account_masters (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT payment_details_tenant_id_fkey FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);