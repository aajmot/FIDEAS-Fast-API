CREATE OR REPLACE FUNCTION initialize_complete_erp_hierarchy()
RETURNS void AS $$
BEGIN
    -- 1. Cleanup
    TRUNCATE TABLE menu_master CASCADE;
    TRUNCATE TABLE module_master CASCADE;

    -- 2. Modules
    INSERT INTO module_master (id, module_name, module_code, description, is_active, is_mandatory)
    VALUES 
    (1, 'ADMIN', 'ADMIN', 'Core system administration and security', true, true),
    (2, 'INVENTORY', 'INVENTORY', 'Generic inventory and supply chain', true, false),
    (3, 'ACCOUNT', 'ACCOUNT', 'Financial accounting and compliance', true, false),
    (4, 'HEALTH', 'HEALTH', 'Clinical and diagnostic services', true, false);

    -- 3. Level 1: Root Menus
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (1000, 'Administration', 'ROOT_ADMIN', 'ADMIN', NULL, '🔧', 1),
    (2000, 'Inventory', 'ROOT_INV', 'INVENTORY', NULL, '📦', 2),
    (3000, 'Finance', 'ROOT_ACC', 'ACCOUNT', NULL, '📊', 3),
    (4000, 'Health Services', 'ROOT_HEALTH', 'HEALTH', NULL, '🏥', 4);

    --------------------------------------------------------------------------------
    -- ADMIN MODULE (Security, Org, and System)
    --------------------------------------------------------------------------------
    -- Level 2: Groups
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (1100, 'Identity & Access', 'ADMIN_ID', 'ADMIN', 1000, '🔐', 1),
    (1200, 'Organization', 'ADMIN_ORG_GRP', 'ADMIN', 1000, '🏢', 2),
    (1300, 'System Config', 'ADMIN_CONFIG_GRP', 'ADMIN', 1000, '⚙️', 3);

    -- Level 3: Actions
    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('User Master', 'USER_MGMT', 'ADMIN', 1100, '/admin/user-management', '👥', 1),
    ('Role Master', 'ROLE_MGMT', 'ADMIN', 1100, '/admin/role-management', '🔐', 2),
    ('User-Role Mapping', 'USER_ROLE_MAPPING', 'ADMIN', 1100, '/admin/user-role-mapping', '🔗', 3),
    ('Menu Access', 'MENU_ACCESS', 'ADMIN', 1100, '/admin/menu-access', '🔒', 4),
    
    ('Legal Entities', 'LEGAL_ENTITY_MGMT', 'ADMIN', 1200, '/admin/legal-entity', '🏢', 1),
    ('Agencies', 'AGENCY_MGMT', 'ADMIN', 1200, '/admin/agency-management', '🏪', 2),
    ('Tenant Update', 'TENANT_UPDATE', 'ADMIN', 1200, '/admin/tenant-update', '🏢', 3),
    
    ('Financial Years', 'FINANCIAL_YEAR', 'ADMIN', 1300, '/admin/financial-years', '📅', 1),
    ('Transaction Templates', 'TRANSACTION_TEMPLATES', 'ADMIN', 1300, '/admin/transaction-templates', '📄', 2),
    ('Currency Management', 'CURRENCY_MGMT', 'ADMIN', 1300, '/admin/currency-management', '💵', 3),
    ('Notifications', 'NOTIFICATIONS', 'ADMIN', 1300, '/admin/notifications', '🔔', 4);

    --------------------------------------------------------------------------------
    -- INVENTORY MODULE (Generic)
    --------------------------------------------------------------------------------
    -- Level 2: Groups
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (2100, 'Masters', 'INV_MSTR_GRP', 'INVENTORY', 2000, '📋', 1),
    (2200, 'Transactions', 'INV_TRANS_GRP', 'INVENTORY', 2000, '📝', 2),
    (2300, 'Stock Reports', 'INV_RPT_GRP', 'INVENTORY', 2000, '📊', 3);

    -- Level 3: Actions
    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Products', 'PRODUCT_MGMT', 'INVENTORY', 2100, '/inventory/product-management', '🏷️', 1),
    ('Categories', 'CATEGORY_MGMT', 'INVENTORY', 2100, '/inventory/category-management', '📂', 2),
    ('Warehouses', 'WAREHOUSES', 'INVENTORY', 2100, '/inventory/warehouses', '🏭', 3),
    ('Units', 'UNIT_MASTER', 'INVENTORY', 2100, '/inventory/unit-management', '📏', 4),
    
    ('Purchase Invoices', 'PURCHASE_INVOICE', 'INVENTORY', 2200, '/inventory/purchase-invoice', '📄', 1),
    ('Sales Invoices', 'SALES_INVOICE', 'INVENTORY', 2200, '/inventory/sales-invoice', '🧾', 2),
    ('Stock Transfers', 'STOCK_TRANSFER', 'INVENTORY', 2200, '/inventory/stock-transfer', '🔄', 3),
    ('Stock Adjustment', 'STOCK_ADJUSTMENT', 'INVENTORY', 2200, '/inventory/stock-adjustment', '🔄', 4),
    
    ('Stock Details', 'STOCK_DETAILS', 'INVENTORY', 2300, '/inventory/stock-details', '📊', 1),
    ('Stock Valuation', 'STOCK_VALUATION', 'INVENTORY', 2300, '/inventory/stock-valuation', '💰', 2),
    ('Stock Aging', 'STOCK_AGING', 'INVENTORY', 2300, '/inventory/stock-aging', '⏰', 3);

    --------------------------------------------------------------------------------
    -- FINANCE MODULE
    --------------------------------------------------------------------------------
    -- Level 2: Groups
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (3100, 'Accounts Setup', 'ACC_MSTR_GRP', 'ACCOUNT', 3000, '📋', 1),
    (3200, 'Vouchers', 'ACC_TRANS_GRP', 'ACCOUNT', 3000, '📝', 2),
    (3300, 'Compliance', 'ACC_COMP_GRP', 'ACCOUNT', 3000, '📋', 3);

    -- Level 3: Actions
    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Chart of Accounts', 'CHART_ACCOUNTS', 'ACCOUNT', 3100, '/account/chart-accounts', '📋', 1),
    ('Account Groups', 'ACCOUNT_GROUPS', 'ACCOUNT', 3100, '/account/account-groups', '📂', 2),
    ('Journal', 'JOURNAL', 'ACCOUNT', 3200, '/account/journal', '📝', 1),
    ('Payments', 'PAYMENTS', 'ACCOUNT', 3200, '/account/payments', '💳', 2),
    ('Receipts', 'RECEIPTS', 'ACCOUNT', 3200, '/account/receipts', '🧾', 3),
    ('GST Reports', 'GST_REPORTS', 'ACCOUNT', 3300, '/account/gst-reports', '📋', 1),
    ('TDS Management', 'TDS_MANAGEMENT', 'ACCOUNT', 3300, '/account/tds-management', '📝', 2);

    --------------------------------------------------------------------------------
    -- HEALTH MODULE (Unified Clinic + Diagnostic)
    --------------------------------------------------------------------------------
    -- Level 2: Groups
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (4100, 'Health Masters', 'HEALTH_MSTR_GRP', 'HEALTH', 4000, '📋', 1),
    (4200, 'Clinical Care', 'CLINIC_TRANS_GRP', 'HEALTH', 4000, '🩺', 2),
    (4300, 'Diagnostics', 'DIAG_TRANS_GRP', 'HEALTH', 4000, '🔬', 3);

    -- Level 3: Actions
    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Patients', 'PATIENT_MGMT', 'HEALTH', 4100, '/clinic/patient-management', '👥', 1),
    ('Doctors', 'DOCTOR_MGMT', 'HEALTH', 4100, '/clinic/doctor-management', '👨‍⚕️', 2),
    ('Test Master', 'CLINIC_TEST_MASTER', 'HEALTH', 4100, '/clinic/test-master', '🧪', 3),
    ('Appointments', 'APPOINTMENT_MGMT', 'HEALTH', 4200, '/clinic/appointments', '📅', 1),
    ('Prescriptions', 'PRESCRIPTION_MGMT', 'HEALTH', 4200, '/clinic/prescriptions', '💊', 2),
    ('Test Orders', 'TEST_ORDER_MGMT', 'HEALTH', 4300, '/diagnostic/test-order', '📋', 1),
    ('Test Results', 'TEST_RESULT_MGMT', 'HEALTH', 4300, '/diagnostic/test-result', '📊', 2);

    -- Reset sequences
    PERFORM setval(pg_get_serial_sequence('module_master', 'id'), COALESCE(MAX(id), 1)) FROM module_master;
    PERFORM setval(pg_get_serial_sequence('menu_master', 'id'), COALESCE(MAX(id), 1)) FROM menu_master;

    RAISE NOTICE 'Complete ERP Hierarchy with all original data initialized.';
END;
$$ LANGUAGE plpgsql;