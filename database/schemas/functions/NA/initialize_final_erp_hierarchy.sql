CREATE OR REPLACE FUNCTION initialize_final_erp_hierarchy()
RETURNS void AS $$
BEGIN
    -- 1. Cleanup
    TRUNCATE TABLE menu_master CASCADE;
    TRUNCATE TABLE module_master CASCADE;

    -- 2. Modules (The Primary Tenant Toggles)
    INSERT INTO module_master (id, module_name, module_code, description, is_active, is_mandatory)
    VALUES 
    (1, 'ADMIN', 'ADMIN', 'Core system administration and security', true, true),
    (2, 'INVENTORY', 'INVENTORY', 'Generic inventory and supply chain', true, false),
    (3, 'ACCOUNT', 'ACCOUNT', 'Financial accounting and compliance', true, false),
    (4, 'HEALTH', 'HEALTH', 'Clinical and diagnostic services', true, false),
    (5, 'DASHBOARD', 'DASHBOARD', 'Reporting and Analytics', true, false);

    -- 3. Level 1: Root Menus (Sidebar)
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (1000, 'Administration', 'ROOT_ADMIN', 'ADMIN', NULL, '🔧', 1),
    (2000, 'Inventory', 'ROOT_INV', 'INVENTORY', NULL, '📦', 2),
    (3000, 'Finance', 'ROOT_ACC', 'ACCOUNT', NULL, '📊', 3),
    (4000, 'Health Services', 'ROOT_HEALTH', 'HEALTH', NULL, '🏥', 4);

    --------------------------------------------------------------------------------
    -- ADMIN MODULE (Complete)
    --------------------------------------------------------------------------------
    -- Level 2: Groups
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (1100, 'Access Control', 'ADMIN_ID', 'ADMIN', 1000, '🔐', 1),
    (1200, 'Organization', 'ADMIN_ORG_GRP', 'ADMIN', 1000, '🏢', 2),
    (1300, 'Global Settings', 'ADMIN_CONFIG_GRP', 'ADMIN', 1000, '⚙️', 3);

    -- Level 3: Actions
    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('User Master', 'USER_MGMT', 'ADMIN', 1100, '/admin/user-management', '👥', 1),
    ('Role Master', 'ROLE_MGMT', 'ADMIN', 1100, '/admin/role-management', '🔐', 2),
    ('User-Role Mapping', 'USER_ROLE_MAPPING', 'ADMIN', 1100, '/admin/user-role-mapping', '🔗', 3),
    ('Menu Access', 'MENU_ACCESS', 'ADMIN', 1100, '/admin/menu-access', '🔒', 4),
    
    ('Legal Entities', 'LEGAL_ENTITY_MGMT', 'ADMIN', 1200, '/admin/legal-entity', '🏢', 1),
    ('Agencies', 'AGENCY_MGMT', 'ADMIN', 1200, '/admin/agency-management', '🏪', 2),
    ('Financial Years', 'FINANCIAL_YEAR', 'ADMIN', 1200, '/admin/financial-years', '📅', 3),
    ('Tenant Update', 'TENANT_UPDATE', 'ADMIN', 1200, '/admin/tenant-update', '🏢', 4),
    
    ('Transaction Templates', 'TRANSACTION_TEMPLATES', 'ADMIN', 1300, '/admin/transaction-templates', '📄', 1),
    ('Account Type Map', 'ACCOUNT_TYPE_MAPPINGS', 'ADMIN', 1300, '/admin/account-type-mappings', '🔗', 2),
    ('Payment Terms', 'PAYMENT_TERMS', 'ADMIN', 1300, '/admin/payment-terms', '💳', 3),
    ('Document Templates', 'DOCUMENT_TEMPLATES', 'ADMIN', 1300, '/admin/document-templates', '📋', 4),
    ('Notifications', 'NOTIFICATIONS', 'ADMIN', 1300, '/admin/notifications', '🔔', 5),
    ('Currency', 'CURRENCY_MANAGEMENT', 'ADMIN', 1300, '/admin/currency-management', '💵', 6);

    --------------------------------------------------------------------------------
    -- INVENTORY MODULE (Verified)
    --------------------------------------------------------------------------------
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (2100, 'Setup', 'INV_MSTR_GRP', 'INVENTORY', 2000, '📋', 1),
    (2200, 'Transactions', 'INV_TRANS_GRP', 'INVENTORY', 2000, '📝', 2),
    (2300, 'Analytics', 'INV_RPT_GRP', 'INVENTORY', 2000, '📊', 3);

    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Categories', 'CATEGORY_MGMT', 'INVENTORY', 2100, '/inventory/category-management', '📂', 1),
    ('Products', 'PRODUCT_MGMT', 'INVENTORY', 2100, '/inventory/product-management', '🏷️', 2),
    ('Batches', 'PRODUCT_BATCH_MGMT', 'INVENTORY', 2100, '/inventory/batch-management', '📎', 3),
    ('Units', 'UNIT_MASTER', 'INVENTORY', 2100, '/inventory/unit-management', '📏', 4),
    ('Warehouses', 'WAREHOUSES', 'INVENTORY', 2100, '/inventory/warehouses', '🏭', 5),
    ('Customers', 'INV_CUSTOMER_MGMT', 'INVENTORY', 2100, '/inventory/customer-management', '👥', 6),
    ('Suppliers', 'SUPPLIER_MGMT', 'INVENTORY', 2100, '/inventory/supplier-management', '🏢', 7),
    
    ('Purchase Invoices', 'PURCHASE_INVOICE', 'INVENTORY', 2200, '/inventory/purchase-invoice', '📄', 1),
    ('Sales Invoices', 'SALES_INVOICE', 'INVENTORY', 2200, '/inventory/sales-invoice', '🧾', 2),
    ('Stock Transfer', 'STOCK_TRANSFER', 'INVENTORY', 2200, '/inventory/stock-transfer', '🔄', 3),
    ('Waste Management', 'PRODUCT_WASTE', 'INVENTORY', 2200, '/inventory/product-waste', '🗑️', 4),
    ('Commissions', 'ORDER_COMMISSION', 'INVENTORY', 2200, '/inventory/order-commission', '💵', 5),
    
    ('Stock Details', 'STOCK_DETAILS', 'INVENTORY', 2300, '/inventory/stock-details', '📊', 1),
    ('Valuation', 'STOCK_VALUATION', 'INVENTORY', 2300, '/inventory/stock-valuation', '💰', 2),
    ('Aging Analysis', 'STOCK_AGING', 'INVENTORY', 2300, '/inventory/stock-aging', '⏰', 3);

    --------------------------------------------------------------------------------
    -- FINANCE MODULE (Accounts - Verified All Items)
    --------------------------------------------------------------------------------
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (3100, 'Accounting Masters', 'ACC_MSTR_GRP', 'ACCOUNT', 3000, '📋', 1),
    (3200, 'Vouchers', 'ACC_TRANS_GRP', 'ACCOUNT', 3000, '📝', 2);

    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Chart of Accounts', 'CHART_ACCOUNTS', 'ACCOUNT', 3100, '/account/chart-accounts', '📖', 1),
    ('Account Groups', 'ACCOUNT_GROUPS', 'ACCOUNT', 3100, '/account/account-groups', '📂', 2),
    ('Cost Centers', 'COST_CENTERS', 'ACCOUNT', 3100, '/account/cost-centers', '🏢', 3),
    
    ('Journal', 'JOURNAL', 'ACCOUNT', 3200, '/account/journal', '📝', 1),
    ('Payments', 'PAYMENTS', 'ACCOUNT', 3200, '/account/payments', '💳', 2),
    ('Receipts', 'RECEIPTS', 'ACCOUNT', 3200, '/account/receipts', '🧾', 3),
    ('Contra', 'CONTRA', 'ACCOUNT', 3200, '/account/contra', '↔️', 4);

    --------------------------------------------------------------------------------
    -- HEALTH MODULE (Unified Clinic & Diagnostic)
    --------------------------------------------------------------------------------
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (4100, 'Setup', 'HEALTH_MSTR_GRP', 'HEALTH', 4000, '📋', 1),
    (4200, 'Operations', 'HEALTH_OPS_GRP', 'HEALTH', 4000, '🔄', 2);

    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Patients', 'PATIENT_MGMT', 'HEALTH', 4100, '/clinic/patient-management', '👥', 1),
    ('Doctors', 'DOCTOR_MGMT', 'HEALTH', 4100, '/clinic/doctor-management', '👨‍⚕️', 2),
    ('Test Categories', 'CLINIC_TEST_CATEGORY', 'HEALTH', 4100, '/clinic/test-category', '📂', 3),
    ('Test Master', 'CLINIC_TEST_MASTER', 'HEALTH', 4100, '/clinic/test-master', '🧪', 4),
    ('Test Panels', 'TEST_PANEL', 'HEALTH', 4100, '/diagnostic/test-panel', '📋', 5),
    ('Billing Master', 'BILLING_MASTER', 'HEALTH', 4100, '/clinic/billing-master', '💰', 6),
    
    ('Appointments', 'APPOINTMENT_MGMT', 'HEALTH', 4200, '/clinic/appointments', '📅', 1),
    ('Medical Records', 'MEDICAL_RECORDS', 'HEALTH', 4200, '/clinic/medical-records', '📋', 2),
    ('Prescriptions', 'PRESCRIPTION_MGMT', 'HEALTH', 4200, '/clinic/prescriptions', '💊', 3),
    ('Lab Orders', 'TEST_ORDER_MGMT', 'HEALTH', 4200, '/diagnostic/test-order', '📋', 4),
    ('Lab Results', 'TEST_RESULT_MGMT', 'HEALTH', 4200, '/diagnostic/test-result', '📊', 5),
    ('Order Commissions', 'DIAG_ORDER_COMMISSION', 'HEALTH', 4200, '/diagnostic/order-commission', '💵', 6);

    -- 4. Sync sequences to prevent primary key errors in future inserts
    PERFORM setval(pg_get_serial_sequence('module_master', 'id'), COALESCE(MAX(id), 1)) FROM module_master;
    PERFORM setval(pg_get_serial_sequence('menu_master', 'id'), COALESCE(MAX(id), 1)) FROM menu_master;

    RAISE NOTICE 'Final Verified ERP Hierarchy Initialized.';
END;
$$ LANGUAGE plpgsql;