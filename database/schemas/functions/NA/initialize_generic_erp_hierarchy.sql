CREATE OR REPLACE FUNCTION initialize_generic_erp_hierarchy()
RETURNS void AS $$
BEGIN
    -- 1. Cleanup existing data
    TRUNCATE TABLE menu_master CASCADE;
    TRUNCATE TABLE module_master CASCADE;

    -- 2. Module Master (The Tenant Enable/Disable Switch)
    INSERT INTO module_master (id, module_name, module_code, description, is_active, is_mandatory)
    VALUES 
    (1, 'ADMIN', 'ADMIN', 'System configuration and user management', true, true),
    (2, 'INVENTORY', 'INVENTORY', 'Generic inventory and supply chain management', true, false),
    (3, 'ACCOUNT', 'ACCOUNT', 'Financial accounting and compliance', true, false),
    (4, 'HEALTH', 'HEALTH', 'Clinical and diagnostic service management', true, false);

    -- 3. Level 1: Root Menus (Sidebar Main Categories)
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (1000, 'Administration', 'ROOT_ADMIN', 'ADMIN', NULL, '⚙️', 1),
    (2000, 'Inventory', 'ROOT_INV', 'INVENTORY', NULL, '📦', 2),
    (3000, 'Finance', 'ROOT_ACC', 'ACCOUNT', NULL, '📊', 3),
    (4000, 'Health Services', 'ROOT_HEALTH', 'HEALTH', NULL, '🏥', 4);

    --------------------------------------------------------------------------------
    -- INVENTORY MODULE (Generic Structure)
    --------------------------------------------------------------------------------
    -- Level 2: Groups
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (2100, 'Setup & Masters', 'INV_MASTERS', 'INVENTORY', 2000, '📋', 1),
    (2200, 'Operations', 'INV_OPS', 'INVENTORY', 2000, '🔄', 2),
    (2300, 'Stock & Reports', 'INV_REPORTS', 'INVENTORY', 2000, '📉', 3);

    -- Level 3: Actions (Generic naming)
    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, sort_order)
    VALUES 
    ('Categories', 'CAT_MGMT', 'INVENTORY', 2100, '/inventory/categories', 1),
    ('Products', 'PROD_MGMT', 'INVENTORY', 2100, '/inventory/products', 2),
    ('Warehouses', 'WH_MGMT', 'INVENTORY', 2100, '/inventory/warehouses', 3),
    ('Purchase Invoices', 'PURCHASE_INV', 'INVENTORY', 2200, '/inventory/purchase', 1),
    ('Sales Invoices', 'SALES_INV', 'INVENTORY', 2200, '/inventory/sales', 2),
    ('Stock Transfers', 'STOCK_TRANS', 'INVENTORY', 2200, '/inventory/transfer', 3),
    ('Current Stock', 'STOCK_LEVELS', 'INVENTORY', 2300, '/inventory/stock-status', 1);

    --------------------------------------------------------------------------------
    -- HEALTH MODULE (Consolidated Clinic & Diagnostic)
    --------------------------------------------------------------------------------
    -- Level 2: Groups
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (4100, 'Registration', 'HEALTH_REG', 'HEALTH', 4000, '👥', 1),
    (4200, 'Clinical', 'HEALTH_CLINIC', 'HEALTH', 4000, '🩺', 2),
    (4300, 'Diagnostics', 'HEALTH_DIAG', 'HEALTH', 4000, '🔬', 3);

    -- Level 3: Actions
    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, sort_order)
    VALUES 
    ('Patients', 'PATIENT_MGMT', 'HEALTH', 4100, '/health/patients', 1),
    ('Practitioners', 'DOC_MGMT', 'HEALTH', 4100, '/health/doctors', 2),
    ('Consultations', 'APP_MGMT', 'HEALTH', 4200, '/health/consultations', 1),
    ('Prescriptions', 'PRES_MGMT', 'HEALTH', 4200, '/health/prescriptions', 2),
    ('Test Orders', 'LAB_ORDERS', 'HEALTH', 4300, '/health/orders', 1),
    ('Test Results', 'LAB_RESULTS', 'HEALTH', 4300, '/health/results', 2);

    -- Sync Sequences
    PERFORM setval(pg_get_serial_sequence('module_master', 'id'), COALESCE(MAX(id), 1)) FROM module_master;
    PERFORM setval(pg_get_serial_sequence('menu_master', 'id'), COALESCE(MAX(id), 1)) FROM menu_master;

    RAISE NOTICE 'Generic ERP Hierarchy Initialized Successfully.';
END;
$$ LANGUAGE plpgsql;