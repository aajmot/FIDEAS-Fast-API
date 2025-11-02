DO $$
BEGIN

IF NOT EXISTS (
    SELECT 1 FROM tenant_settings 
    WHERE tenant_id = 1 AND setting = 'base_currency'
) THEN

INSERT INTO tenant_settings (tenant_id, setting, description, value_type, value, created_at, created_by, updated_at, updated_by)
VALUES (1, 'base_currency', 'Base currency for the tenant', 'TEXT', 'INR', NOW(), 'system', NOW(), 'system');

END IF;

END $$;