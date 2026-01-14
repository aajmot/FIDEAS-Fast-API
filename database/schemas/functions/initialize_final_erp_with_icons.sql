CREATE OR REPLACE FUNCTION initialize_final_erp_with_icons()
RETURNS void AS $$
BEGIN
    -- 1. Cleanup
    TRUNCATE TABLE menu_master CASCADE;
    TRUNCATE TABLE module_master CASCADE;
    TRUNCATE TABLE currencies CASCADE;

    -- 2. Modules
    INSERT INTO module_master (id, module_name, module_code, description, is_active, is_mandatory)
    VALUES 
    (1, 'ADMIN', 'ADMIN', 'Core system and security', true, true),
    (2, 'INVENTORY', 'INVENTORY', 'Supply chain and stock', true, false),
    (3, 'ACCOUNT', 'ACCOUNT', 'Finance and compliance', true, false),
    (4, 'HEALTH', 'HEALTH', 'Clinical and diagnostics', true, false),
    (5, 'PEOPLE', 'PEOPLE', 'People and Operations', true, false);

    -- 3. Level 1: Root Menus
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (1000, 'Admin', 'ROOT_ADMIN', 'ADMIN', NULL, '🛠️', 1),
    (2000, 'Inventory', 'ROOT_INV', 'INVENTORY', NULL, '📦', 2),
    (3000, 'Finance', 'ROOT_ACC', 'ACCOUNT', NULL, '💰', 3),
    (4000, 'Health', 'ROOT_HEALTH', 'HEALTH', NULL, '🏥', 4),
    (5000, 'People', 'ROOT_PEOPLE', 'PEOPLE', NULL, '👥', 5);

    --------------------------------------------------------------------------------
    -- ADMIN (Identity, Org, Settings)
    --------------------------------------------------------------------------------
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (1100, 'Identity', 'ADMIN_ID', 'ADMIN', 1000, '🔐', 1),
    (1200, 'Organization', 'ADMIN_ORG_GRP', 'ADMIN', 1000, '🏢', 2),
    (1300, 'Settings', 'ADMIN_CONFIG_GRP', 'ADMIN', 1000, '⚙️', 3);

    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Users', 'USER_MGMT', 'ADMIN', 1100, '/admin/user-management', '👥', 1),
    ('Roles', 'ROLE_MGMT', 'ADMIN', 1100, '/admin/role-management', '🛡️', 2),
    ('Permissions', 'MENU_ACCESS', 'ADMIN', 1100, '/admin/menu-access', '🔑', 3),
    ('Mapping', 'USER_ROLE_MAPPING', 'ADMIN', 1100, '/admin/user-role-mapping', '🔗', 4),
    
    ('Entities', 'LEGAL_ENTITY_MGMT', 'ADMIN', 1200, '/admin/legal-entity', '🏛️', 1),
    ('Agencies', 'AGENCY_MGMT', 'ADMIN', 1200, '/admin/agency-management', '🏪', 2),
    ('Tenants', 'TENANT_UPDATE', 'ADMIN', 1200, '/admin/tenant-update', '🌐', 3),
    ('Years', 'FINANCIAL_YEAR', 'ADMIN', 1200, '/admin/financial-years', '📅', 4),
    
    ('Templates', 'TRANSACTION_TEMPLATES', 'ADMIN', 1300, '/admin/transaction-templates', '📄', 1),
    ('Documents', 'DOCUMENT_TEMPLATES', 'ADMIN', 1300, '/admin/document-templates', '📂', 2),
    ('Currency', 'CURRENCY_MGMT', 'ADMIN', 1300, '/admin/currency-management', '💵', 3),
    ('Payments', 'PAYMENT_TERMS', 'ADMIN', 1300, '/admin/payment-terms', '💳', 4),
    ('Alerts', 'NOTIFICATIONS', 'ADMIN', 1300, '/admin/notifications', '🔔', 5);

    --------------------------------------------------------------------------------
    -- INVENTORY (Setup, Ops, Reports)
    --------------------------------------------------------------------------------
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (2100, 'Setup', 'INV_MSTR_GRP', 'INVENTORY', 2000, '🏗️', 1),
    (2200, 'Transactions', 'INV_TRANS_GRP', 'INVENTORY', 2000, '🔄', 2),
    (2300, 'Reports', 'INV_RPT_GRP', 'INVENTORY', 2000, '📈', 3);

    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Products', 'PRODUCT_MGMT', 'INVENTORY', 2100, '/inventory/product-management', '🏷️', 1),
    ('Batches', 'PRODUCT_BATCH_MGMT', 'INVENTORY', 2100, '/inventory/batch-management', '🔢', 2),
    ('Categories', 'CATEGORY_MGMT', 'INVENTORY', 2100, '/inventory/category-management', '🗂️', 3),
    ('Units', 'UNIT_MASTER', 'INVENTORY', 2100, '/inventory/unit-management', '📏', 4),
    ('Warehouses', 'WAREHOUSES', 'INVENTORY', 2100, '/inventory/warehouses', '🏭', 5),
    ('Customers', 'INV_CUSTOMER_MGMT', 'INVENTORY', 2100, '/inventory/customer-management', '👤', 6),
    
    ('Purchase', 'PURCHASE_INVOICE', 'INVENTORY', 2200, '/inventory/purchase-invoice', '📥', 1),
    ('Sales', 'SALES_INVOICE', 'INVENTORY', 2200, '/inventory/sales-invoice', '📤', 2),
    ('Transfer', 'STOCK_TRANSFER', 'INVENTORY', 2200, '/inventory/stock-transfer', '🚚', 3),
    ('Adjustment', 'STOCK_ADJUSTMENT', 'INVENTORY', 2200, '/inventory/stock-adjustment', '🛠️', 4),
    ('Waste', 'PRODUCT_WASTE', 'INVENTORY', 2200, '/inventory/product-waste', '🗑️', 5),
    ('Commissions', 'ORDER_COMMISSION', 'INVENTORY', 2200, '/inventory/order-commission', '💸', 6),
    
    ('Levels', 'STOCK_DETAILS', 'INVENTORY', 2300, '/inventory/stock-details', '📊', 1),
    ('Valuation', 'STOCK_VALUATION', 'INVENTORY', 2300, '/inventory/stock-valuation', '💎', 2),
    ('Aging', 'STOCK_AGING', 'INVENTORY', 2300, '/inventory/stock-aging', '⏳', 3);

    --------------------------------------------------------------------------------
    -- FINANCE (Masters, Vouchers, Books, Assets, Tax)
    --------------------------------------------------------------------------------
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (3100, 'Masters', 'ACC_MSTR_GRP', 'ACCOUNT', 3000, '📁', 1),
    (3200, 'Vouchers', 'ACC_TRANS_GRP', 'ACCOUNT', 3000, '📝', 2),
    (3300, 'Books', 'ACC_BOOKS_GRP', 'ACCOUNT', 3000, '📚', 3),
    (3400, 'Assets', 'ACC_ASSETS_GRP', 'ACCOUNT', 3000, '🏢', 4),
    (3500, 'Tax', 'ACC_TAX_GRP', 'ACCOUNT', 3000, '⚖️', 5);

    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Accounts', 'CHART_ACCOUNTS', 'ACCOUNT', 3100, '/account/chart-accounts', '📒', 1),
    ('Groups', 'ACCOUNT_GROUPS', 'ACCOUNT', 3100, '/account/account-groups', '📂', 2),
    ('Series', 'VOUCHER_SERIES', 'ACCOUNT', 3100, '/account/voucher-series', '🔢', 3),
    ('Reconcile', 'BANK_RECONCILIATION', 'ACCOUNT', 3100, '/account/bank-reconciliation', '🏦', 4),
    
    ('Journal', 'JOURNAL', 'ACCOUNT', 3200, '/account/journal', '📓', 1),
    ('Payments', 'PAYMENTS', 'ACCOUNT', 3200, '/account/payments', '💸', 2),
    ('Receipts', 'RECEIPTS', 'ACCOUNT', 3200, '/account/receipts', '🧾', 3),
    ('Contra', 'CONTRA', 'ACCOUNT', 3200, '/account/contra', '🔄', 4),
    ('CreditNotes', 'CREDIT_NOTES', 'ACCOUNT', 3200, '/account/credit-notes', '➖', 5),
    ('DebitNotes', 'DEBIT_NOTES', 'ACCOUNT', 3200, '/account/debit-notes', '➕', 6),
    
    ('Ledger', 'LEDGER', 'ACCOUNT', 3300, '/account/ledger', '📖', 1),
    ('Cashbook', 'CASH_BOOK', 'ACCOUNT', 3300, '/account/cash-book', '💵', 2),
    ('Daybook', 'DAY_BOOK', 'ACCOUNT', 3300, '/account/day-book', '🗓️', 3),
    
    ('FixedAssets', 'FIXED_ASSETS', 'ACCOUNT', 3400, '/account/fixed-assets', '🏗️', 1),
    ('Depreciation', 'DEPRECIATION', 'ACCOUNT', 3400, '/account/depreciation', '📉', 2),
    
    ('GST', 'GST_REPORTS', 'ACCOUNT', 3500, '/account/gst-reports', '📓', 1),
    ('E-Invoice', 'EINVOICE', 'ACCOUNT', 3500, '/account/einvoice', '📧', 2),
    ('TDS', 'TDS_RETURNS', 'ACCOUNT', 3500, '/account/tds-returns', '📑', 3);

    --------------------------------------------------------------------------------
    -- HEALTH (Setup, Clinical, Laboratory)
    --------------------------------------------------------------------------------
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (4100, 'Setup', 'HEALTH_MSTR_GRP', 'HEALTH', 4000, '⚙️', 1),
    (4200, 'Clinical', 'HEALTH_CLINIC_GRP', 'HEALTH', 4000, '🩺', 2),
    (4300, 'Laboratory', 'HEALTH_LAB_GRP', 'HEALTH', 4000, '🔬', 3),
    (4400, 'Finance', 'HEALTH_FINANCE', 'HEALTH', 4000, '💰', 4)
    ;

    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Patients', 'PATIENT_MGMT', 'HEALTH', 4100, '/clinic/patient-management', '👤', 1),
    ('Doctors', 'DOCTOR_MGMT', 'HEALTH', 4100, '/clinic/doctor-management', '👨‍⚕️', 2),
    ('Catalog', 'CLINIC_TEST_MASTER', 'HEALTH', 4100, '/clinic/test-master', '🧪', 3),
    ('Panels', 'TEST_PANEL', 'HEALTH', 4100, '/diagnostic/test-panel', '📋', 4),
    ('Billing', 'BILLING_MASTER', 'HEALTH', 4100, '/clinic/billing-master', '💰', 5),
    
    ('Appointments', 'APPOINTMENT_MGMT', 'HEALTH', 4200, '/clinic/appointments', '📅', 1),
    ('Records', 'MEDICAL_RECORDS', 'HEALTH', 4200, '/clinic/medical-records', '📁', 2),
    ('Prescriptions', 'PRESCRIPTION_MGMT', 'HEALTH', 4200, '/clinic/prescriptions', '💊', 3),
    ('Invoices', 'APPOINTMENT_INVOICE', 'HEALTH', 4200, '/health/appointment-invoice', '📋', 4),
    
    
    ('Orders', 'TEST_ORDER_MGMT', 'HEALTH', 4300, '/diagnostic/test-order', '📝', 1),
    ('Invoices', 'TEST_INVOICE_MGMT', 'HEALTH', 4300, '/health/test-invoice', '💰', 2),
    ('Results', 'TEST_RESULT_MGMT', 'HEALTH', 4300, '/diagnostic/test-result', '📊', 3),
    ('Fees', 'DIAG_ORDER_COMMISSION', 'HEALTH', 4300, '/diagnostic/order-commission', '💸', 4),
    
    ('Advance', 'HEALTH_ADVANCE_PAYMENT', 'HEALTH', 4400, '/health/payment/advance', '💰', 1),
    ('Invoice', 'HEALTH_INVOICE_PAYMENT', 'HEALTH', 4400, '/health/payment/invoice', '📝', 2),
    ('Allocation', 'HEALTH_PAYMENT_ALLOCATION', 'HEALTH', 4400, '/health/payment/allocation', '💸', 3)
    
    ;
    
    --------------------------------------------------------------------------------
    -- PEOPLE (People and Operations)
    --------------------------------------------------------------------------------    
    INSERT INTO menu_master (id, menu_name, menu_code, module_code, parent_menu_id, icon, sort_order)
    VALUES 
    (5100, 'Setup', 'PEOPLE_MSTR_GRP', 'PEOPLE', 5000, '⚙️', 1)
    ;

    INSERT INTO menu_master (menu_name, menu_code, module_code, parent_menu_id, route, icon, sort_order)
    VALUES 
    ('Department', 'PEOPLE_DEPT', 'PEOPLE', 5100, '/people/departments', '📊', 1),
    ('Employee', 'PEOPLE_EMP', 'PEOPLE', 5100, '/people/employees', '👨‍⚕️', 2)
    ;



    -- 4. Currency 
    INSERT INTO currencies (
    id, code, name, symbol, is_base, is_active, 
    created_at, created_by, updated_at, updated_by, is_deleted
    )
    VALUES 
    (1, 'INR', 'Indian Rupee', N'₹', true, true, '2025-10-20 22:07:14.76208', 'system', '2025-10-22 23:43:51.19427', 'system', false)
    -- ,(2, 'USD', 'US Dollar', '$', false, false, '2025-10-20 22:07:14.76208', 'system', '2025-10-22 23:43:51.19427', 'system', true),
    -- (3, 'EUR', 'Euro', '€', false, false, '2025-10-20 22:07:14.76208', 'system', '2025-10-22 23:43:51.19427', 'system', true),
    -- (4, 'GBP', 'British Pound', '£', false, false, '2025-10-20 22:07:14.76208', 'system', '2025-10-22 23:43:51.19427', 'system', true),
    -- (5, 'AED', 'UAE Dirham', N'د.إ', false, false, '2025-10-20 22:07:14.76208', 'system', '2025-10-22 23:43:51.19427', 'system', true)
    ;

    -- 5. Sync sequences
    PERFORM setval(pg_get_serial_sequence('module_master', 'id'), COALESCE(MAX(id), 1)) FROM module_master;
    PERFORM setval(pg_get_serial_sequence('menu_master', 'id'), COALESCE(MAX(id), 1)) FROM menu_master;
    PERFORM setval(pg_get_serial_sequence('currencies', 'id'), COALESCE(MAX(id), 1)) FROM currencies;


    RAISE NOTICE 'Complete Hierarchical ERP with Icons Initialized.';
END;
$$ LANGUAGE plpgsql;