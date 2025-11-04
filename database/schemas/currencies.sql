DROP TABLE IF EXISTS public.currencies;
CREATE TABLE IF NOT EXISTS public.currencies
(
    id SERIAL PRIMARY KEY,
    code character varying(3)  NOT NULL,
    name character varying(50)  NOT NULL,
    symbol character varying(5) ,
    is_base boolean DEFAULT false,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(100)  DEFAULT 'system'::character varying,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by character varying(100)  DEFAULT 'system'::character varying,
    is_deleted boolean DEFAULT false,
    
    
    CONSTRAINT currencies_code_key UNIQUE (code)
)
