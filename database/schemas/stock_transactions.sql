-- Table: public.stock_transactions

DROP TABLE IF EXISTS public.stock_transactions;

CREATE TABLE IF NOT EXISTS public.stock_transactions
(
    id SERIAL PRIMARY KEY,
    product_id integerNOT NULL,
    transaction_type character varying(20) NOT NULL,
    transaction_source character varying(200) NOT NULL,
    reference_id integerNOT NULL,
    reference_number character varying(200) NOT NULL,
    batch_number character varying(200) ,
    quantity numeric(10,2)NOT NULL,
    unit_price numeric(10,2)NOT NULL,
    transaction_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tenant_id integerNOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(200) ,
    expiry_date date,
    manufacturing_date date,
    warehouse_id integer
);