-- =====================================================
-- Stored Procedure: Initialize Accounting Data for New Tenant
-- =====================================================
-- Purpose: Creates complete accounting structure for a new tenant including:
--   1. Account Groups (Asset, Liability, Equity, Revenue, Expense)
--   2. System Account Masters (Chart of Accounts)
--   3. Account Configuration Keys
--   4. Account Configurations (Mappings)
--   5. Transaction Templates with Rules
--
-- Usage: SELECT initialize_tenant_accounting(tenant_id, created_by);
-- Example: SELECT initialize_tenant_accounting(2, 'admin@example.com');
-- =====================================================

DROP FUNCTION IF EXISTS initialize_tenant_accounting(INTEGER, VARCHAR);

CREATE OR REPLACE FUNCTION initialize_tenant_accounting(
    p_tenant_id INTEGER,
    p_created_by VARCHAR DEFAULT 'system'
)
RETURNS TABLE(
    status VARCHAR,
    message TEXT,
    account_groups_count INTEGER,
    account_masters_count INTEGER,
    config_keys_count INTEGER,
    configurations_count INTEGER,
    templates_count INTEGER,
    voucher_types_count INTEGER
) AS $$
DECLARE
    v_account_groups_count INTEGER := 0;
    v_account_masters_count INTEGER := 0;
    v_config_keys_count INTEGER := 0;
    v_configurations_count INTEGER := 0;
    v_templates_count INTEGER := 0;
    v_voucher_types_count INTEGER := 0;
    
    -- Account Group IDs
    v_asset_group_id INTEGER;
    v_liability_group_id INTEGER;
    v_equity_group_id INTEGER;
    v_revenue_group_id INTEGER;
    v_expense_group_id INTEGER;
    
    -- Account Master IDs (for configurations)
    v_cash_id INTEGER;
    v_bank_id INTEGER;
    v_ar_id INTEGER;
    v_ap_id INTEGER;
    v_inventory_id INTEGER;
    v_sales_id INTEGER;
    v_purchase_expense_id INTEGER;
    v_cgst_input_id INTEGER;
    v_sgst_input_id INTEGER;
    v_igst_input_id INTEGER;
    v_cgst_output_id INTEGER;
    v_sgst_output_id INTEGER;
    v_igst_output_id INTEGER;
    v_sales_return_id INTEGER;
    v_purchase_return_id INTEGER;
    v_discount_received_id INTEGER;
    v_discount_given_id INTEGER;
    v_waste_loss_id INTEGER;
    v_clinic_revenue_id INTEGER;
    v_diagnostic_revenue_id INTEGER;
    v_comm_sales_id INTEGER;
    v_comm_clinic_id INTEGER;
    v_comm_diagn_id INTEGER;
    v_patient_advance_id INTEGER;
    
    -- Configuration Key IDs
    v_key_cash_id INTEGER;
    v_key_bank_id INTEGER;
    v_key_ar_id INTEGER;
    v_key_ap_id INTEGER;
    v_key_inventory_id INTEGER;
    v_key_sales_id INTEGER;
    v_key_purchase_id INTEGER;
    v_key_cgst_input_id INTEGER;
    v_key_sgst_input_id INTEGER;
    v_key_igst_input_id INTEGER;
    v_key_cgst_output_id INTEGER;
    v_key_sgst_output_id INTEGER;
    v_key_igst_output_id INTEGER;
    v_key_waste_expense_id INTEGER;
    v_key_patient_advance_id INTEGER;
    v_key_clinic_revenue_id INTEGER;
    v_key_diagnostic_revenue_id INTEGER;
    
    -- Module IDs
    v_inventory_module_id INTEGER;
    v_accounting_module_id INTEGER;
    v_clinic_module_id INTEGER;
    v_diagnostic_module_id INTEGER;
    
    -- Template IDs
    v_template_purchase_id INTEGER;
    v_template_sales_id INTEGER;
    v_template_payment_id INTEGER;
    v_template_receipt_id INTEGER;
    v_template_test_invoice_id INTEGER;
    v_template_advance_receipt_id INTEGER;
    v_template_advance_allocation_id INTEGER;
    
BEGIN
    -- Validate tenant exists
    IF NOT EXISTS (SELECT 1 FROM tenants WHERE id = p_tenant_id) THEN
        RETURN QUERY SELECT 'ERROR'::VARCHAR, 
            'Tenant ID ' || p_tenant_id || ' does not exist'::TEXT,
            0::INTEGER, 0::INTEGER, 0::INTEGER, 0::INTEGER, 0::INTEGER, 0::INTEGER;
        RETURN;
    END IF;
    
    -- Delete existing accounting data for this tenant (if reinitializing)
    -- This will cascade delete related configurations, transaction templates, etc.
    RAISE NOTICE 'Deleting existing accounting data for tenant %', p_tenant_id;
    
    DELETE FROM transaction_template_rules WHERE template_id IN (SELECT id FROM transaction_templates WHERE tenant_id = p_tenant_id);
    DELETE FROM transaction_templates WHERE tenant_id = p_tenant_id;
    DELETE FROM account_configurations WHERE tenant_id = p_tenant_id;
    DELETE FROM account_masters WHERE tenant_id = p_tenant_id;
    DELETE FROM account_groups WHERE tenant_id = p_tenant_id;
    DELETE FROM voucher_types WHERE tenant_id = p_tenant_id;
    
    RAISE NOTICE 'Existing data deleted, proceeding with fresh initialization';
    
    -- Get module IDs (global, not tenant-specific)
    SELECT id INTO v_inventory_module_id FROM module_master WHERE module_code = 'INVENTORY';
    SELECT id INTO v_accounting_module_id FROM module_master WHERE module_code = 'ACCOUNTING';
    SELECT id INTO v_clinic_module_id FROM module_master WHERE module_code = 'CLINIC';
    SELECT id INTO v_diagnostic_module_id FROM module_master WHERE module_code = 'DIAGNOSTIC';
    
    -- =====================================================
    -- 1. CREATE ACCOUNT GROUPS
    -- =====================================================
    
    -- Assets
    INSERT INTO account_groups (tenant_id, account_type, name, code, parent_id, is_system_assigned, is_active, created_by)
    VALUES (p_tenant_id, 'ASSET', 'Assets', 'ASET', NULL, TRUE, TRUE, p_created_by)
    RETURNING id INTO v_asset_group_id;
    
    -- Liabilities
    INSERT INTO account_groups (tenant_id, account_type, name, code, parent_id, is_system_assigned, is_active, created_by)
    VALUES (p_tenant_id, 'LIABILITY', 'Liabilities', 'LIAB', NULL, TRUE, TRUE, p_created_by)
    RETURNING id INTO v_liability_group_id;
    
    -- Equity
    INSERT INTO account_groups (tenant_id, account_type, name, code, parent_id, is_system_assigned, is_active, created_by)
    VALUES (p_tenant_id, 'EQUITY', 'Equity', 'EQTY', NULL, TRUE, TRUE, p_created_by)
    RETURNING id INTO v_equity_group_id;
    
    -- Revenue
    INSERT INTO account_groups (tenant_id, account_type, name, code, parent_id, is_system_assigned, is_active, created_by)
    VALUES (p_tenant_id, 'REVENUE', 'Revenue', 'REVN', NULL, TRUE, TRUE, p_created_by)
    RETURNING id INTO v_revenue_group_id;
    
    -- Expense
    INSERT INTO account_groups (tenant_id, account_type, name, code, parent_id, is_system_assigned, is_active, created_by)
    VALUES (p_tenant_id, 'EXPENSE', 'Expenses', 'EXPN', NULL, TRUE, TRUE, p_created_by)
    RETURNING id INTO v_expense_group_id;
    
    v_account_groups_count := 5;
    
    -- =====================================================
    -- 2. CREATE ACCOUNT MASTERS (CHART OF ACCOUNTS)
    -- =====================================================
    
    -- ASSETS
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_asset_group_id, '1010-CASH', 'Cash Account', 'Main cash account', 'ASSET', 'D', TRUE, 'CASH', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_cash_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_asset_group_id, '1020-BANK', 'Bank Account', 'Main bank account', 'ASSET', 'D', TRUE, 'BANK', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_bank_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_asset_group_id, '1100-AR', 'Accounts Receivable', 'Customer receivables', 'ASSET', 'D', TRUE, 'ACCOUNTS_RECEIVABLE', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_ar_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_asset_group_id, '1200-INV', 'Inventory', 'Inventory asset account', 'ASSET', 'D', TRUE, 'INVENTORY', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_inventory_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_asset_group_id, '1310-GST-CGST-IN', 'CGST Input Credit', 'CGST recoverable on purchases', 'ASSET', 'D', TRUE, 'GST_INPUT_CGST', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_cgst_input_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_asset_group_id, '1320-GST-SGST-IN', 'SGST Input Credit', 'SGST recoverable on purchases', 'ASSET', 'D', TRUE, 'GST_INPUT_SGST', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_sgst_input_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_asset_group_id, '1330-GST-IGST-IN', 'IGST Input Credit', 'IGST recoverable on purchases', 'ASSET', 'D', TRUE, 'GST_INPUT_IGST', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_igst_input_id;
    
    -- LIABILITIES
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_liability_group_id, '2100-AP', 'Accounts Payable', 'Vendor payables', 'LIABILITY', 'C', TRUE, 'ACCOUNTS_PAYABLE', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_ap_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_liability_group_id, '2200-PAT-ADV', 'Patient Advance', 'Patient advance payments', 'LIABILITY', 'C', TRUE, 'PATIENT_ADVANCE', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_patient_advance_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_liability_group_id, '2310-GST-CGST-OUT', 'CGST Payable', 'CGST output tax payable', 'LIABILITY', 'C', TRUE, 'GST_OUTPUT_CGST', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_cgst_output_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_liability_group_id, '2320-GST-SGST-OUT', 'SGST Payable', 'SGST output tax payable', 'LIABILITY', 'C', TRUE, 'GST_OUTPUT_SGST', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_sgst_output_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_liability_group_id, '2330-GST-IGST-OUT', 'IGST Payable', 'IGST output tax payable', 'LIABILITY', 'C', TRUE, 'GST_OUTPUT_IGST', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_igst_output_id;
    
    -- EQUITY
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_equity_group_id, '3100-EQUITY', 'Owner Equity', 'Owner capital account', 'EQUITY', 'C', TRUE, 'OWNER_EQUITY', 1, 0, 0, TRUE, p_created_by);
    
    -- REVENUE
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_revenue_group_id, '4100-SALES', 'Sales Revenue', 'Product sales revenue', 'REVENUE', 'C', TRUE, 'SALES', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_sales_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_revenue_group_id, '4200-CLINIC', 'Clinic Revenue', 'Clinic services revenue', 'REVENUE', 'C', TRUE, 'CLINIC_REVENUE', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_clinic_revenue_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_revenue_group_id, '4300-DIAGNOSTIC', 'Diagnostic Revenue', 'Diagnostic services revenue', 'REVENUE', 'C', TRUE, 'DIAGNOSTIC_REVENUE', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_diagnostic_revenue_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_revenue_group_id, '4910-SALES-RET', 'Sales Returns', 'Sales returns and allowances', 'REVENUE', 'D', TRUE, 'SALES_RETURN', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_sales_return_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_revenue_group_id, '4920-DISC-REC', 'Discount Received', 'Discounts received from suppliers', 'REVENUE', 'C', TRUE, 'DISCOUNT_RECEIVED', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_discount_received_id;
    
    -- EXPENSE
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_expense_group_id, '5100-PURCHASE', 'Purchase Expense', 'Cost of goods purchased', 'EXPENSE', 'D', TRUE, 'PURCHASE', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_purchase_expense_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_expense_group_id, '5910-PUR-RET', 'Purchase Returns', 'Purchase returns to suppliers', 'EXPENSE', 'C', TRUE, 'PURCHASE_RETURN', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_purchase_return_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_expense_group_id, '5300-DISC-GIVEN', 'Discount Allowed', 'Discounts given to customers', 'EXPENSE', 'D', TRUE, 'DISCOUNT_GIVEN', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_discount_given_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_expense_group_id, '5200-WASTE', 'Waste Loss', 'Inventory waste and loss', 'EXPENSE', 'D', TRUE, 'WASTE_LOSS', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_waste_loss_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_expense_group_id, '5800-GEN-EXP', 'General Expense', 'Miscellaneous expenses', 'EXPENSE', 'D', TRUE, 'GENERAL_EXPENSE', 1, 0, 0, TRUE, p_created_by);
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_expense_group_id, '5900-OP-EXP', 'Operating Expense', 'Operating costs', 'EXPENSE', 'D', TRUE, 'OPERATING_EXPENSE', 1, 0, 0, TRUE, p_created_by);
    
    -- Agent Commission Accounts
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_expense_group_id, '5710-COMM-SALES', 'Agent Commission - Sales', 'Commission on product sales', 'EXPENSE', 'D', TRUE, 'COMMISSION_SALES', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_comm_sales_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_expense_group_id, '5720-COMM-CLINIC', 'Agent Commission - Clinic', 'Commission on clinic services', 'EXPENSE', 'D', TRUE, 'COMMISSION_CLINIC', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_comm_clinic_id;
    
    INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, account_type, normal_balance, is_system_account, system_code, level, opening_balance, current_balance, is_active, created_by)
    VALUES (p_tenant_id, v_expense_group_id, '5730-COMM-DIAG', 'Agent Commission - Diagnostics', 'Commission on diagnostic services', 'EXPENSE', 'D', TRUE, 'COMMISSION_DIAGNOSTIC', 1, 0, 0, TRUE, p_created_by)
    RETURNING id INTO STRICT v_comm_diagn_id;
    
    v_account_masters_count := 27;
    
    -- =====================================================
    -- 2.1 VALIDATE ALL ACCOUNT IDS RETRIEVED
    -- =====================================================
    
    -- Validate that all required account IDs were successfully retrieved
    IF v_cash_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve cash account ID';
    END IF;
    IF v_bank_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve bank account ID';
    END IF;
    IF v_ar_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve accounts receivable ID';
    END IF;
    IF v_ap_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve accounts payable ID';
    END IF;
    IF v_inventory_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve inventory account ID';
    END IF;
    IF v_sales_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve sales account ID';
    END IF;
    IF v_purchase_expense_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve purchase expense account ID';
    END IF;
    IF v_cgst_input_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve CGST input account ID';
    END IF;
    IF v_sgst_input_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve SGST input account ID';
    END IF;
    IF v_igst_input_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve IGST input account ID';
    END IF;
    IF v_cgst_output_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve CGST output account ID';
    END IF;
    IF v_sgst_output_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve SGST output account ID';
    END IF;
    IF v_igst_output_id IS NULL THEN
        RAISE EXCEPTION 'Failed to retrieve IGST output account ID';
    END IF;
    
    -- =====================================================
    -- 3. CREATE ACCOUNT CONFIGURATION KEYS (IF NOT EXISTS)
    -- =====================================================
    
    -- These are global configuration keys, not tenant-specific
    -- Use ON CONFLICT to make this idempotent
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES 
    ('WASTE_EXPENSE', 'Waste Expense Account', 'Account for recording product waste and spoilage expenses', TRUE),
    ('PATIENT_ADVANCE', 'Patient Advance Account', 'Account for tracking patient advance payments', TRUE),
    ('CLINIC_REVENUE', 'Clinic Revenue Account', 'Account for clinic services revenue', TRUE),
    ('DIAGNOSTIC_REVENUE', 'Diagnostic Revenue Account', 'Account for diagnostic services revenue', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_cash_id FROM account_configuration_keys WHERE code = 'CASH';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('BANK', 'Bank Account', 'Default bank account for banking transactions', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_bank_id FROM account_configuration_keys WHERE code = 'BANK';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('ACCOUNTS_RECEIVABLE', 'Accounts Receivable', 'Customer receivables account', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_ar_id FROM account_configuration_keys WHERE code = 'ACCOUNTS_RECEIVABLE';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('ACCOUNTS_PAYABLE', 'Accounts Payable', 'Vendor payables account', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_ap_id FROM account_configuration_keys WHERE code = 'ACCOUNTS_PAYABLE';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('INVENTORY', 'Inventory Account', 'Inventory asset account', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_inventory_id FROM account_configuration_keys WHERE code = 'INVENTORY';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('SALES', 'Sales Revenue', 'Sales revenue account', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_sales_id FROM account_configuration_keys WHERE code = 'SALES';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('PURCHASE', 'Purchase Expense', 'Purchase expense account', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_purchase_id FROM account_configuration_keys WHERE code = 'PURCHASE';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('GST_INPUT_CGST', 'CGST Input', 'CGST input tax credit', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_cgst_input_id FROM account_configuration_keys WHERE code = 'GST_INPUT_CGST';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('GST_INPUT_SGST', 'SGST Input', 'SGST input tax credit', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_sgst_input_id FROM account_configuration_keys WHERE code = 'GST_INPUT_SGST';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('GST_INPUT_IGST', 'IGST Input', 'IGST input tax credit', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_igst_input_id FROM account_configuration_keys WHERE code = 'GST_INPUT_IGST';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('GST_OUTPUT_CGST', 'CGST Output', 'CGST output tax payable', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_cgst_output_id FROM account_configuration_keys WHERE code = 'GST_OUTPUT_CGST';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('GST_OUTPUT_SGST', 'SGST Output', 'SGST output tax payable', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_sgst_output_id FROM account_configuration_keys WHERE code = 'GST_OUTPUT_SGST';
    
    INSERT INTO account_configuration_keys (code, name, description, is_active)
    VALUES ('GST_OUTPUT_IGST', 'IGST Output', 'IGST output tax payable', TRUE)
    ON CONFLICT (code) DO NOTHING;
    SELECT id INTO v_key_igst_output_id FROM account_configuration_keys WHERE code = 'GST_OUTPUT_IGST';
    
    SELECT id INTO v_key_waste_expense_id FROM account_configuration_keys WHERE code = 'WASTE_EXPENSE';
    SELECT id INTO v_key_patient_advance_id FROM account_configuration_keys WHERE code = 'PATIENT_ADVANCE';
    SELECT id INTO v_key_clinic_revenue_id FROM account_configuration_keys WHERE code = 'CLINIC_REVENUE';
    SELECT id INTO v_key_diagnostic_revenue_id FROM account_configuration_keys WHERE code = 'DIAGNOSTIC_REVENUE';
    
    -- Update default_account_id for configuration keys (global defaults)
    UPDATE account_configuration_keys SET default_account_id = v_cash_id WHERE code = 'CASH' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_bank_id WHERE code = 'BANK' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_ar_id WHERE code = 'ACCOUNTS_RECEIVABLE' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_ap_id WHERE code = 'ACCOUNTS_PAYABLE' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_inventory_id WHERE code = 'INVENTORY' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_sales_id WHERE code = 'SALES' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_purchase_expense_id WHERE code = 'PURCHASE' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_cgst_input_id WHERE code = 'GST_INPUT_CGST' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_sgst_input_id WHERE code = 'GST_INPUT_SGST' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_igst_input_id WHERE code = 'GST_INPUT_IGST' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_cgst_output_id WHERE code = 'GST_OUTPUT_CGST' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_sgst_output_id WHERE code = 'GST_OUTPUT_SGST' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_igst_output_id WHERE code = 'GST_OUTPUT_IGST' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_waste_loss_id WHERE code = 'WASTE_EXPENSE' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_patient_advance_id WHERE code = 'PATIENT_ADVANCE' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_clinic_revenue_id WHERE code = 'CLINIC_REVENUE' AND default_account_id IS NULL;
    UPDATE account_configuration_keys SET default_account_id = v_diagnostic_revenue_id WHERE code = 'DIAGNOSTIC_REVENUE' AND default_account_id IS NULL;
    
    -- Count new keys created (approximate)
    SELECT COUNT(*) INTO v_config_keys_count 
    FROM account_configuration_keys 
    WHERE code IN ('CASH', 'BANK', 'ACCOUNTS_RECEIVABLE', 'ACCOUNTS_PAYABLE', 'INVENTORY', 
                   'SALES', 'PURCHASE', 'GST_INPUT_CGST', 'GST_INPUT_SGST', 'GST_INPUT_IGST',
                   'GST_OUTPUT_CGST', 'GST_OUTPUT_SGST', 'GST_OUTPUT_IGST', 'WASTE_EXPENSE',
                   'PATIENT_ADVANCE', 'CLINIC_REVENUE', 'DIAGNOSTIC_REVENUE');
    
    -- =====================================================
    -- 4. CREATE ACCOUNT CONFIGURATIONS (TENANT-SPECIFIC MAPPINGS)
    -- =====================================================
    
    -- Debug: Log account IDs
    RAISE NOTICE 'Account IDs - Cash:%, Bank:%, AR:%, AP:%, Inv:%, Sales:%, Purchase:%, CGST_In:%, SGST_In:%, IGST_In:%, CGST_Out:%, SGST_Out:%, IGST_Out:%',
        v_cash_id, v_bank_id, v_ar_id, v_ap_id, v_inventory_id, v_sales_id, v_purchase_expense_id,
        v_cgst_input_id, v_sgst_input_id, v_igst_input_id, v_cgst_output_id, v_sgst_output_id, v_igst_output_id;
    
    -- Verify all accounts exist
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_cash_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'Cash account ID % does not exist for tenant %', v_cash_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_bank_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'Bank account ID % does not exist for tenant %', v_bank_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_ar_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'AR account ID % does not exist for tenant %', v_ar_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_ap_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'AP account ID % does not exist for tenant %', v_ap_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_inventory_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'Inventory account ID % does not exist for tenant %', v_inventory_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_sales_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'Sales account ID % does not exist for tenant %', v_sales_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_purchase_expense_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'Purchase expense account ID % does not exist for tenant %', v_purchase_expense_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_cgst_input_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'CGST input account ID % does not exist for tenant %', v_cgst_input_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_sgst_input_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'SGST input account ID % does not exist for tenant %', v_sgst_input_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_igst_input_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'IGST input account ID % does not exist for tenant %', v_igst_input_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_cgst_output_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'CGST output account ID % does not exist for tenant %', v_cgst_output_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_sgst_output_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'SGST output account ID % does not exist for tenant %', v_sgst_output_id, p_tenant_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM account_masters WHERE id = v_igst_output_id AND tenant_id = p_tenant_id) THEN
        RAISE EXCEPTION 'IGST output account ID % does not exist for tenant %', v_igst_output_id, p_tenant_id;
    END IF;
    
    INSERT INTO account_configurations (tenant_id, config_key_id, account_id, module, created_by)
    VALUES 
        (p_tenant_id, v_key_cash_id, v_cash_id, NULL, p_created_by),
        (p_tenant_id, v_key_bank_id, v_bank_id, NULL, p_created_by),
        (p_tenant_id, v_key_ar_id, v_ar_id, NULL, p_created_by),
        (p_tenant_id, v_key_ap_id, v_ap_id, NULL, p_created_by),
        (p_tenant_id, v_key_inventory_id, v_inventory_id, 'INVENTORY', p_created_by),
        (p_tenant_id, v_key_sales_id, v_sales_id, 'INVENTORY', p_created_by),
        (p_tenant_id, v_key_purchase_id, v_purchase_expense_id, 'INVENTORY', p_created_by),
        (p_tenant_id, v_key_cgst_input_id, v_cgst_input_id, NULL, p_created_by),
        (p_tenant_id, v_key_sgst_input_id, v_sgst_input_id, NULL, p_created_by),
        (p_tenant_id, v_key_igst_input_id, v_igst_input_id, NULL, p_created_by),
        (p_tenant_id, v_key_cgst_output_id, v_cgst_output_id, NULL, p_created_by),
        (p_tenant_id, v_key_sgst_output_id, v_sgst_output_id, NULL, p_created_by),
        (p_tenant_id, v_key_igst_output_id, v_igst_output_id, NULL, p_created_by),
        (p_tenant_id, v_key_waste_expense_id, v_waste_loss_id, 'INVENTORY', p_created_by),
        (p_tenant_id, v_key_patient_advance_id, v_patient_advance_id, 'DIAGNOSTIC', p_created_by),
        (p_tenant_id, v_key_clinic_revenue_id, v_clinic_revenue_id, 'CLINIC', p_created_by),
        (p_tenant_id, v_key_diagnostic_revenue_id, v_diagnostic_revenue_id, 'DIAGNOSTIC', p_created_by);
    
    v_configurations_count := 17;
    
    -- =====================================================
    -- 5. CREATE VOUCHER TYPES
    -- =====================================================
    
    -- Standard voucher types with tax and commission support
    INSERT INTO voucher_types (tenant_id, name, code, prefix, allow_multi_currency, allow_tax, allow_commission, is_active, created_by)
    VALUES 
        (p_tenant_id, 'Purchase', 'PURCHASE', 'PUR', TRUE, TRUE, TRUE, TRUE, p_created_by),
        (p_tenant_id, 'Sales', 'SALES', 'SAL', TRUE, TRUE, TRUE, TRUE, p_created_by),
        (p_tenant_id, 'Payment', 'PAYMENT', 'PAY', TRUE, FALSE, FALSE, TRUE, p_created_by),
        (p_tenant_id, 'Receipt', 'RECEIPT', 'REC', TRUE, FALSE, FALSE, TRUE, p_created_by),
        (p_tenant_id, 'Journal', 'JOURNAL', 'JNL', TRUE, FALSE, FALSE, TRUE, p_created_by),
        (p_tenant_id, 'Contra', 'CONTRA', 'CNTR', FALSE, FALSE, FALSE, TRUE, p_created_by),
        (p_tenant_id, 'Credit Note', 'CREDIT_NOTE', 'CN', TRUE, TRUE, FALSE, TRUE, p_created_by),
        (p_tenant_id, 'Debit Note', 'DEBIT_NOTE', 'DN', TRUE, TRUE, FALSE, TRUE, p_created_by);
    
    v_voucher_types_count := 8;
    
    -- =====================================================
    -- 6. CREATE TRANSACTION TEMPLATES
    -- =====================================================
    
    -- Purchase Invoice Template
    INSERT INTO transaction_templates (tenant_id, module_id, transaction_type, code, name, description, is_active, created_by)
    VALUES (p_tenant_id, v_inventory_module_id, 'PURCHASE_INVOICE', 'TMP_PURCHASE', 'Purchase Invoice Template', 
            'Standard template for purchase invoices', TRUE, p_created_by)
    RETURNING id INTO STRICT v_template_purchase_id;
    
    -- Purchase Invoice Rules
    INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_active, created_by)
    VALUES 
        (p_tenant_id, v_template_purchase_id, 1, 'EXPENSE', v_purchase_expense_id, 'DEBIT', 'item.amount', 'Purchase expense', TRUE, p_created_by),
        (p_tenant_id, v_template_purchase_id, 2, 'ASSET', v_cgst_input_id, 'DEBIT', 'item.cgst_amount', 'CGST input', TRUE, p_created_by),
        (p_tenant_id, v_template_purchase_id, 3, 'ASSET', v_sgst_input_id, 'DEBIT', 'item.sgst_amount', 'SGST input', TRUE, p_created_by),
        (p_tenant_id, v_template_purchase_id, 4, 'ASSET', v_igst_input_id, 'DEBIT', 'item.igst_amount', 'IGST input', TRUE, p_created_by),
        (p_tenant_id, v_template_purchase_id, 5, 'LIABILITY', v_ap_id, 'CREDIT', 'invoice.total_amount', 'Accounts payable', TRUE, p_created_by);
    
    -- Sales Invoice Template
    INSERT INTO transaction_templates (tenant_id, module_id, transaction_type, code, name, description, is_active, created_by)
    VALUES (p_tenant_id, v_inventory_module_id, 'SALES_INVOICE', 'TMP_SALES', 'Sales Invoice Template', 
            'Standard template for sales invoices', TRUE, p_created_by)
    RETURNING id INTO STRICT v_template_sales_id;
    
    -- Sales Invoice Rules
    INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_active, created_by)
    VALUES 
        (p_tenant_id, v_template_sales_id, 1, 'ASSET', v_ar_id, 'DEBIT', 'invoice.total_amount', 'Accounts receivable', TRUE, p_created_by),
        (p_tenant_id, v_template_sales_id, 2, 'REVENUE', v_sales_id, 'CREDIT', 'item.amount', 'Sales revenue', TRUE, p_created_by),
        (p_tenant_id, v_template_sales_id, 3, 'LIABILITY', v_cgst_output_id, 'CREDIT', 'item.cgst_amount', 'CGST output', TRUE, p_created_by),
        (p_tenant_id, v_template_sales_id, 4, 'LIABILITY', v_sgst_output_id, 'CREDIT', 'item.sgst_amount', 'SGST output', TRUE, p_created_by),
        (p_tenant_id, v_template_sales_id, 5, 'LIABILITY', v_igst_output_id, 'CREDIT', 'item.igst_amount', 'IGST output', TRUE, p_created_by);
    
    -- Payment Template
    INSERT INTO transaction_templates (tenant_id, module_id, transaction_type, code, name, description, is_active, created_by)
    VALUES (p_tenant_id, v_accounting_module_id, 'PAYMENT', 'TMP_PAYMENT', 'Payment Template', 
            'Standard template for payments', TRUE, p_created_by)
    RETURNING id INTO STRICT v_template_payment_id;
    
    -- Payment Rules
    INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_active, created_by)
    VALUES 
        (p_tenant_id, v_template_payment_id, 1, 'LIABILITY', v_ap_id, 'DEBIT', 'payment.amount', 'Payment to vendor', TRUE, p_created_by),
        (p_tenant_id, v_template_payment_id, 2, 'ASSET', v_cash_id, 'CREDIT', 'payment.amount', 'Cash payment', TRUE, p_created_by);
    
    -- Receipt Template
    INSERT INTO transaction_templates (tenant_id, module_id, transaction_type, code, name, description, is_active, created_by)
    VALUES (p_tenant_id, v_accounting_module_id, 'RECEIPT', 'TMP_RECEIPT', 'Receipt Template', 
            'Standard template for receipts', TRUE, p_created_by)
    RETURNING id INTO STRICT v_template_receipt_id;
    
    -- Receipt Rules
    INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_active, created_by)
    VALUES 
        (p_tenant_id, v_template_receipt_id, 1, 'ASSET', v_cash_id, 'DEBIT', 'receipt.amount', 'Cash receipt', TRUE, p_created_by),
        (p_tenant_id, v_template_receipt_id, 2, 'ASSET', v_ar_id, 'CREDIT', 'receipt.amount', 'Receipt from customer', TRUE, p_created_by);
    
    -- Test Invoice Template
    INSERT INTO transaction_templates (tenant_id, module_id, transaction_type, code, name, description, is_active, created_by)
    VALUES (p_tenant_id, v_diagnostic_module_id, 'TEST_INVOICE', 'TMP_TEST_INV', 'Test Invoice Template', 
            'Template for diagnostic test invoices', TRUE, p_created_by)
    RETURNING id INTO STRICT v_template_test_invoice_id;
    
    -- Test Invoice Rules
    INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_active, created_by)
    VALUES 
        (p_tenant_id, v_template_test_invoice_id, 1, 'ASSET', v_ar_id, 'DEBIT', 'invoice.final_amount', 'Accounts receivable', TRUE, p_created_by),
        (p_tenant_id, v_template_test_invoice_id, 2, 'REVENUE', v_diagnostic_revenue_id, 'CREDIT', 'invoice.taxable_amount', 'Diagnostic revenue', TRUE, p_created_by),
        (p_tenant_id, v_template_test_invoice_id, 3, 'LIABILITY', v_cgst_output_id, 'CREDIT', 'invoice.cgst_amount', 'CGST output', TRUE, p_created_by),
        (p_tenant_id, v_template_test_invoice_id, 4, 'LIABILITY', v_sgst_output_id, 'CREDIT', 'invoice.sgst_amount', 'SGST output', TRUE, p_created_by),
        (p_tenant_id, v_template_test_invoice_id, 5, 'LIABILITY', v_igst_output_id, 'CREDIT', 'invoice.igst_amount', 'IGST output', TRUE, p_created_by);
    
    -- Advance Receipt Template
    INSERT INTO transaction_templates (tenant_id, module_id, transaction_type, code, name, description, is_active, created_by)
    VALUES (p_tenant_id, v_accounting_module_id, 'ADVANCE_RECEIPT', 'TMP_ADV_REC', 'Advance Receipt Template', 
            'Template for patient advance payments', TRUE, p_created_by)
    RETURNING id INTO STRICT v_template_advance_receipt_id;
    
    -- Advance Receipt Rules
    INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_active, created_by)
    VALUES 
        (p_tenant_id, v_template_advance_receipt_id, 1, 'ASSET', v_cash_id, 'DEBIT', 'payment.amount', 'Cash received', TRUE, p_created_by),
        (p_tenant_id, v_template_advance_receipt_id, 2, 'LIABILITY', v_patient_advance_id, 'CREDIT', 'payment.amount', 'Patient advance', TRUE, p_created_by);
    
    -- Advance Allocation Template
    INSERT INTO transaction_templates (tenant_id, module_id, transaction_type, code, name, description, is_active, created_by)
    VALUES (p_tenant_id, v_accounting_module_id, 'ADVANCE_ALLOCATION', 'TMP_ADV_ALLOC', 'Advance Allocation Template', 
            'Template for allocating advance to invoice', TRUE, p_created_by)
    RETURNING id INTO STRICT v_template_advance_allocation_id;
    
    -- Advance Allocation Rules
    INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_active, created_by)
    VALUES 
        (p_tenant_id, v_template_advance_allocation_id, 1, 'LIABILITY', v_patient_advance_id, 'DEBIT', 'allocation.amount', 'Advance adjusted', TRUE, p_created_by),
        (p_tenant_id, v_template_advance_allocation_id, 2, 'ASSET', v_ar_id, 'CREDIT', 'allocation.amount', 'AR reduced', TRUE, p_created_by);
    
    v_templates_count := 7;
    
    -- =====================================================
    -- RETURN SUCCESS
    -- =====================================================
    
    RETURN QUERY SELECT 
        'SUCCESS'::VARCHAR,
        'Accounting data initialized successfully for tenant ' || p_tenant_id::TEXT,
        v_account_groups_count,
        v_account_masters_count,
        v_config_keys_count,
        v_configurations_count,
        v_templates_count,
        v_voucher_types_count;
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT 
            'ERROR'::VARCHAR,
            'Failed to initialize accounting data: ' || SQLERRM::TEXT,
            0::INTEGER, 0::INTEGER, 0::INTEGER, 0::INTEGER, 0::INTEGER, 0::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- USAGE EXAMPLES
-- =====================================================
-- 
-- Initialize accounting for tenant 2:
-- SELECT * FROM initialize_tenant_accounting(2, 'admin@company.com');
--
-- Initialize accounting for tenant 3 with system user:
-- SELECT * FROM initialize_tenant_accounting(3);
--
-- Check results:
-- SELECT status, message, 
--        account_groups_count, account_masters_count, 
--        config_keys_count, configurations_count, templates_count, voucher_types_count
-- FROM initialize_tenant_accounting(2, 'admin@company.com');
-- =====================================================
