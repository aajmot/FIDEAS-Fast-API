-- Migration script to add missing audit columns to tables
-- Based on BaseModel standard: is_active, created_at, created_by, updated_at, updated_by, is_deleted

BEGIN;

-- Tables missing audit columns completely
ALTER TABLE public.approval_levels 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.bank_reconciliation_items 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.clinic_invoice_items 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.credit_note_items 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.debit_note_items 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.eway_bills 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.inventory 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.journal_details 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.notification_logs 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.purchase_order_items 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.purchase_invoice_items 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.sales_invoice_items 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.sales_order_items 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.stock_transfer_items 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.user_roles 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.voucher_types 
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

-- Tables with partial audit columns - adding missing ones
ALTER TABLE public.account_groups 
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.approval_history 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.approval_requests 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.currencies 
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.dashboard_widgets 
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.depreciation_schedule 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.document_attachments 
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.exchange_rates 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.gst_configuration 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.gstr1_data 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.journals 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.ledgers 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.medical_records 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.menu_master 
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.module_master 
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.payments 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.prescriptions 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.product_batches 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.product_waste 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.role_menu_mapping 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.scheduled_reports 
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.stock_balances 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.stock_by_location 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.stock_meter 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.subcategories 
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.tds_deductions 
ADD COLUMN is_active boolean DEFAULT true,
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.tds_rates 
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

ALTER TABLE public.tenants 
ADD COLUMN created_by character varying(100) DEFAULT 'system',
ADD COLUMN updated_by character varying(100) DEFAULT 'system',
ADD COLUMN is_deleted boolean DEFAULT false;

-- Fix naming inconsistencies
ALTER TABLE public.agencies RENAME COLUMN modified_at TO updated_at;
ALTER TABLE public.agencies RENAME COLUMN modified_by TO updated_by;
ALTER TABLE public.agencies RENAME COLUMN is_delete TO is_deleted;

COMMIT;