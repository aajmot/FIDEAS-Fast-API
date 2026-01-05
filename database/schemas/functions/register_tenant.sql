CREATE OR REPLACE FUNCTION register_tenant(
    p_tenant_name VARCHAR DEFAULT 'ROSE PHARMACY',
    p_tenant_code VARCHAR DEFAULT 'RP',
    p_tenant_tagline VARCHAR DEFAULT '',
    p_tenant_address VARCHAR DEFAULT 'AHMEDABAD,GUJRAJ,INDIA,380000',
    p_business_type VARCHAR DEFAULT 'TRADING',
    p_admin_username VARCHAR DEFAULT 'rp_admin',
    p_admin_email VARCHAR DEFAULT 'rp_admin@mail.com',
    p_admin_password_hash VARCHAR DEFAULT '$2b$12$N4JugIoPjvtC5tdXPbqOU.ZkD7MVI4nlPLBLMLJfE1vmT2CmR360i',
    p_admin_first_name VARCHAR DEFAULT 'John',
    p_admin_last_name VARCHAR DEFAULT 'Bhai'
)
RETURNS TABLE(
    tenant_id INTEGER,
    admin_user_id INTEGER,
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    v_tenant_id INTEGER;
    v_admin_user_id INTEGER;
    v_admin_role_id INTEGER;
    v_module_record RECORD;
    v_enable_inventory VARCHAR := 'TRUE';
BEGIN
    -- Validate business_type
    IF p_business_type NOT IN ('TRADING', 'SERVICE', 'HYBRID') THEN
        RAISE EXCEPTION 'business_type must be TRADING, SERVICE, or HYBRID';
    END IF;

    -- Check if tenant code exists
    IF EXISTS (SELECT 1 FROM tenants WHERE code = p_tenant_code) THEN
        RAISE EXCEPTION 'Tenant code already exists';
    END IF;

    -- Check if username exists
    IF EXISTS (SELECT 1 FROM users WHERE username = p_admin_username) THEN
        RAISE EXCEPTION 'Username already exists';
    END IF;

    -- Set enable_inventory based on business_type
    IF p_business_type = 'SERVICE' THEN
        v_enable_inventory := 'FALSE';
    END IF;

    -- 1. Create tenant
    INSERT INTO tenants (name, code, tagline, address, business_type, created_at)
    VALUES (p_tenant_name, p_tenant_code, p_tenant_tagline, p_tenant_address, p_business_type, NOW())
    RETURNING id INTO v_tenant_id;

    -- 2. Create admin role
    INSERT INTO roles (name, description, tenant_id, created_by)
    VALUES ('Admin', 'System Administrator', v_tenant_id, 'system')
    RETURNING id INTO v_admin_role_id;

    -- 3. Create admin user
    INSERT INTO users (username, email, first_name, last_name, password_hash, tenant_id, is_tenant_admin, created_by)
    VALUES (p_admin_username, p_admin_email, p_admin_first_name, p_admin_last_name, p_admin_password_hash, v_tenant_id, TRUE, 'system')
    RETURNING id INTO v_admin_user_id;

    -- 4. Assign admin role to user
    INSERT INTO user_roles (user_id, role_id, tenant_id, created_by)
    VALUES (v_admin_user_id, v_admin_role_id, v_tenant_id, 'system');

    -- 5. Assign all active modules to tenant
    FOR v_module_record IN SELECT id FROM module_master WHERE is_active = TRUE
    LOOP
        INSERT INTO tenant_module_mapping (tenant_id, module_id, is_active, created_by)
        VALUES (v_tenant_id, v_module_record.id, TRUE, 'system');
    END LOOP;

    -- 6. Create default tenant settings (static configuration)
    INSERT INTO tenant_settings (tenant_id, setting, description, value_type, value, created_by)
    VALUES 
        (v_tenant_id, 'enable_inventory', 'use stock and COGS entry', 'BOOLEAN', v_enable_inventory, 'system'),
        (v_tenant_id, 'enable_gst', 'Apply gst calculation', 'BOOLEAN', 'TRUE', 'system'),
        (v_tenant_id, 'enable_bank_entry', 'Auto create bank receipt/payment', 'BOOLEAN', 'TRUE', 'system'),
        (v_tenant_id, 'base_currency', 'Base currency for the tenant', 'CURRENCY', 'INR', 'system');

    -- Return results
    RETURN QUERY SELECT v_tenant_id, v_admin_user_id, TRUE, 'Tenant registration completed successfully'::TEXT;

EXCEPTION
    WHEN OTHERS THEN
        -- Return error
        RETURN QUERY SELECT NULL::INTEGER, NULL::INTEGER, FALSE, SQLERRM::TEXT;
END;
$$ LANGUAGE plpgsql;
