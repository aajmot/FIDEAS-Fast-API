delete from public.tenant_settings cascade;

INSERT INTO public.tenant_settings (tenant_id, setting, description, value_type, value, created_at, created_by, updated_at, updated_by) VALUES
(1, 'enable_inventory', 'use stock and COGS entry', 'BOOLEAN', 'TRUE', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP, 'system'),
(1, 'enable_gst', 'Apply gst calculation', 'BOOLEAN', 'TRUE', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP, 'system'),
(1, 'enable_bank_entry', 'Auto create bank receipt/payment', 'BOOLEAN', 'TRUE', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP, 'system'),
(1, 'base_currency', 'Base currency for the tenant', 'CURRENCY', 'INR', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP, 'system')
;


INSERT INTO public.tenant_settings (tenant_id, setting, description, value_type, value, created_at, created_by, updated_at, updated_by) VALUES
(2, 'enable_inventory', 'use stock and COGS entry', 'BOOLEAN', 'TRUE', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP, 'system'),
(2, 'enable_gst', 'Apply gst calculation', 'BOOLEAN', 'TRUE', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP, 'system'),
(2, 'enable_bank_entry', 'Auto create bank receipt/payment', 'BOOLEAN', 'TRUE', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP, 'system'),
(2, 'base_currency', 'Base currency for the tenant', 'CURRENCY', 'INR', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP, 'system')
;