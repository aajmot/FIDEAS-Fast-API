-- =====================================================
-- Function: Reinitialize Transaction Templates for Tenant
-- =====================================================
DROP FUNCTION IF EXISTS reinitialize_transaction_templates(INTEGER);

CREATE OR REPLACE FUNCTION reinitialize_transaction_templates(p_tenant_id INTEGER)
RETURNS TABLE(status VARCHAR, message TEXT, templates_count INTEGER, rules_count INTEGER) AS $$
DECLARE
    v_templates_count INTEGER := 0;
    v_rules_count INTEGER := 0;
BEGIN
    -- Validate tenant exists
    IF NOT EXISTS (SELECT 1 FROM tenants WHERE id = p_tenant_id) THEN
        RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Tenant does not exist'::TEXT, 0::INTEGER, 0::INTEGER;
        RETURN;
    END IF;
    
    -- Delete existing templates and rules
    DELETE FROM transaction_template_rules WHERE template_id IN (SELECT id FROM transaction_templates WHERE tenant_id = p_tenant_id);
    DELETE FROM transaction_templates WHERE tenant_id = p_tenant_id;
    
    -- Insert transaction templates
    INSERT INTO transaction_templates (tenant_id, module_id, transaction_type, code, name, description)
    VALUES
    (p_tenant_id, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'SALES_INVOICE',      'TT001', 'Sales Invoice Template',          'Template for customer sales invoices'),
    (p_tenant_id, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'PURCHASE_INVOICE',    'TT002', 'Purchase Invoice Template',       'Template for vendor purchase invoices'),
    (p_tenant_id, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'STOCK_ADJUSTMENT',    'TT003', 'Stock Adjustment Template',       'Template for inventory adjustments'),
    (p_tenant_id, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'PRODUCT_WASTED',      'TT004', 'Product Wasted Template',         'Template for recording wasted/damaged items'),
    (p_tenant_id, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'DEBIT_NOTE',          'TT008', 'Debit Note Template',             'Template for issuing debit note to supplier'),
    (p_tenant_id, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'CREDIT_NOTE',         'TT009', 'Credit Note Template',            'Template for issuing credit note to customer'),
    (p_tenant_id, (SELECT id FROM module_master WHERE module_code = 'ACCOUNT'), 'SALES_PAYMENT',       'TT005', 'Sales Payment Template',          'Template for receiving customer payments'),
    (p_tenant_id, (SELECT id FROM module_master WHERE module_code = 'ACCOUNT'), 'PURCHASE_PAYMENT',    'TT006', 'Purchase Payment Template',       'Template for making vendor payments'),
    (p_tenant_id, (SELECT id FROM module_master WHERE module_code = 'HEALTH'), 'PATIENT_BILL',        'TT007', 'Patient Bill Template',           'Template for patient billing'),
    (p_tenant_id, (SELECT id FROM module_master WHERE module_code = 'HEALTH'), 'DIAGNOSTIC_BILL',     'TT010', 'Diagnostic Bill Template',        'Template for diagnostic services billing')
    ON CONFLICT (tenant_id, code) DO NOTHING;
    
    GET DIAGNOSTICS v_templates_count = ROW_COUNT;
    
    -- Insert template rules
    INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
    VALUES
    -- SALES_INVOICE
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = p_tenant_id), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = '1100-AR' AND tenant_id = p_tenant_id), 'CREDIT', 'NET_AMOUNT', 'Invoice {{ref}} | {{line_items}}', TRUE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = p_tenant_id), 2, 'INCOME', (SELECT id FROM account_masters WHERE code = '4100-SALES' AND tenant_id = p_tenant_id), 'DEBIT', 'TAXABLE_AMOUNT', 'Sales: {{line_items}}', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = p_tenant_id), 3, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2310-GST-CGST-OUT' AND tenant_id = p_tenant_id), 'DEBIT', 'CGST_AMOUNT', 'CGST @{{cgst_rate}}% on {{line_items}}', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = p_tenant_id), 4, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2320-GST-SGST-OUT' AND tenant_id = p_tenant_id), 'DEBIT', 'SGST_AMOUNT', 'SGST @{{sgst_rate}}% on {{line_items}}', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = p_tenant_id), 5, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2330-GST-IGST-OUT' AND tenant_id = p_tenant_id), 'DEBIT', 'IGST_AMOUNT', 'IGST @{{igst_rate}}% on {{line_items}}', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = p_tenant_id), 6, 'INCOME', (SELECT id FROM account_masters WHERE code = '5300-DISC-GIVEN' AND tenant_id = p_tenant_id), 'CREDIT', 'TOTAL_DISCOUNT', 'Discount Allowed', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = p_tenant_id), 7, 'EXPENSE', (SELECT id FROM account_masters WHERE code = '5710-COMM-SALES' AND tenant_id = p_tenant_id), 'DEBIT', 'AGENT_COMMISSION', 'Agent Commission @{{agent_commission_percent}}% - {{agent_name}}', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = p_tenant_id), 8, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2100-AP' AND tenant_id = p_tenant_id), 'CREDIT', 'AGENT_COMMISSION', 'Payable to Agent {{agent_name}}', TRUE),
    -- PURCHASE_INVOICE
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = p_tenant_id), 1, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2100-AP' AND tenant_id = p_tenant_id), 'DEBIT', 'NET_AMOUNT', 'Bill {{ref}} | {{line_items}}', TRUE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = p_tenant_id), 2, 'EXPENSE', (SELECT id FROM account_masters WHERE code = '5100-PURCHASE' AND tenant_id = p_tenant_id), 'CREDIT', 'TAXABLE_AMOUNT', 'Purchase: {{line_items}}', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = p_tenant_id), 3, 'ASSET', (SELECT id FROM account_masters WHERE code = '1310-GST-CGST-IN' AND tenant_id = p_tenant_id), 'CREDIT', 'CGST_AMOUNT', 'CGST Input @{{cgst_rate}}%', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = p_tenant_id), 4, 'ASSET', (SELECT id FROM account_masters WHERE code = '1320-GST-SGST-IN' AND tenant_id = p_tenant_id), 'CREDIT', 'SGST_AMOUNT', 'SGST Input @{{sgst_rate}}%', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = p_tenant_id), 5, 'ASSET', (SELECT id FROM account_masters WHERE code = '1330-GST-IGST-IN' AND tenant_id = p_tenant_id), 'CREDIT', 'IGST_AMOUNT', 'IGST Input @{{igst_rate}}%', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = p_tenant_id), 6, 'INCOME', (SELECT id FROM account_masters WHERE code = '4920-DISC-REC' AND tenant_id = p_tenant_id), 'DEBIT', 'TOTAL_DISCOUNT', 'Discount Received', FALSE),
    -- STOCK_ADJUSTMENT
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'STOCK_ADJUSTMENT' AND tenant_id = p_tenant_id), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = '1200-INV' AND tenant_id = p_tenant_id), 'DEBIT', 'TOTAL_AMOUNT', 'Inventory Increase', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'STOCK_ADJUSTMENT' AND tenant_id = p_tenant_id), 2, 'EXPENSE', (SELECT id FROM account_masters WHERE code = '5200-WASTE' AND tenant_id = p_tenant_id), 'CREDIT', 'TOTAL_AMOUNT', 'Adjustment Expense (if loss)', FALSE),
    -- PRODUCT_WASTED
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PRODUCT_WASTED' AND tenant_id = p_tenant_id), 1, 'EXPENSE', (SELECT id FROM account_masters WHERE code = '5200-WASTE' AND tenant_id = p_tenant_id), 'DEBIT', 'TOTAL_AMOUNT', 'Waste / Scrap Loss', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PRODUCT_WASTED' AND tenant_id = p_tenant_id), 2, 'ASSET', (SELECT id FROM account_masters WHERE code = '1200-INV' AND tenant_id = p_tenant_id), 'CREDIT', 'TOTAL_AMOUNT', 'Inventory Reduction', FALSE),
    -- SALES_PAYMENT
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_PAYMENT' AND tenant_id = p_tenant_id), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = '1020-BANK' AND tenant_id = p_tenant_id), 'DEBIT', 'TOTAL_AMOUNT_FCY', 'Payment {{ref}} in {{currency}}', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_PAYMENT' AND tenant_id = p_tenant_id), 2, 'ASSET', (SELECT id FROM account_masters WHERE code = '1100-AR' AND tenant_id = p_tenant_id), 'CREDIT', 'TOTAL_AMOUNT_BASE', 'Customer Payment (Base)', TRUE),
    -- PURCHASE_PAYMENT
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_PAYMENT' AND tenant_id = p_tenant_id), 1, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2100-AP' AND tenant_id = p_tenant_id), 'DEBIT', 'TOTAL_AMOUNT_BASE', 'Vendor Payment (Base)', TRUE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_PAYMENT' AND tenant_id = p_tenant_id), 2, 'ASSET', (SELECT id FROM account_masters WHERE code = '1020-BANK' AND tenant_id = p_tenant_id), 'CREDIT', 'TOTAL_AMOUNT_FCY', 'Payment {{ref}} in {{currency}}', FALSE),
    -- PATIENT_BILL
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = p_tenant_id), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = '1100-AR' AND tenant_id = p_tenant_id), 'DEBIT', 'NET_AMOUNT', 'Patient Bill {{ref}}', TRUE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = p_tenant_id), 2, 'INCOME', (SELECT id FROM account_masters WHERE code = '4200-CLINIC' AND tenant_id = p_tenant_id), 'CREDIT', 'TAXABLE_AMOUNT', 'Clinic Services', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = p_tenant_id), 3, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2310-GST-CGST-OUT' AND tenant_id = p_tenant_id), 'CREDIT', 'CGST_AMOUNT', 'CGST @{{cgst_rate}}%', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = p_tenant_id), 4, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2320-GST-SGST-OUT' AND tenant_id = p_tenant_id), 'CREDIT', 'SGST_AMOUNT', 'SGST @{{sgst_rate}}%', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = p_tenant_id), 5, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2330-GST-IGST-OUT' AND tenant_id = p_tenant_id), 'CREDIT', 'IGST_AMOUNT', 'IGST @{{igst_rate}}%', FALSE),
    -- DIAGNOSTIC_BILL
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = p_tenant_id), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = '1100-AR' AND tenant_id = p_tenant_id), 'DEBIT', 'NET_AMOUNT', 'Diagnostic Bill {{ref}}', TRUE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = p_tenant_id), 2, 'INCOME', (SELECT id FROM account_masters WHERE code = '4300-DIAGNOSTIC' AND tenant_id = p_tenant_id), 'CREDIT', 'TAXABLE_AMOUNT', 'Diagnostic Services', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = p_tenant_id), 3, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2310-GST-CGST-OUT' AND tenant_id = p_tenant_id), 'CREDIT', 'CGST_AMOUNT', 'CGST @{{cgst_rate}}%', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = p_tenant_id), 4, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2320-GST-SGST-OUT' AND tenant_id = p_tenant_id), 'CREDIT', 'SGST_AMOUNT', 'SGST @{{sgst_rate}}%', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = p_tenant_id), 5, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2330-GST-IGST-OUT' AND tenant_id = p_tenant_id), 'CREDIT', 'IGST_AMOUNT', 'IGST @{{igst_rate}}%', FALSE),
    -- DEBIT_NOTE
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = p_tenant_id), 1, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2100-AP' AND tenant_id = p_tenant_id), 'DEBIT', 'NET_AMOUNT', 'Debit Note {{ref}}', TRUE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = p_tenant_id), 2, 'EXPENSE', (SELECT id FROM account_masters WHERE code = '5100-PURCHASE' AND tenant_id = p_tenant_id), 'CREDIT', 'TAXABLE_AMOUNT', 'Purchase Return', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = p_tenant_id), 3, 'ASSET', (SELECT id FROM account_masters WHERE code = '1310-GST-CGST-IN' AND tenant_id = p_tenant_id), 'CREDIT', 'CGST_AMOUNT', 'CGST Reversal', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = p_tenant_id), 4, 'ASSET', (SELECT id FROM account_masters WHERE code = '1320-GST-SGST-IN' AND tenant_id = p_tenant_id), 'CREDIT', 'SGST_AMOUNT', 'SGST Reversal', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = p_tenant_id), 5, 'ASSET', (SELECT id FROM account_masters WHERE code = '1330-GST-IGST-IN' AND tenant_id = p_tenant_id), 'CREDIT', 'IGST_AMOUNT', 'IGST Reversal', FALSE),
    -- CREDIT_NOTE
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = p_tenant_id), 1, 'INCOME', (SELECT id FROM account_masters WHERE code = '4100-SALES' AND tenant_id = p_tenant_id), 'DEBIT', 'TAXABLE_AMOUNT', 'Sales Return', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = p_tenant_id), 2, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2310-GST-CGST-OUT' AND tenant_id = p_tenant_id), 'DEBIT', 'CGST_AMOUNT', 'CGST Reversal', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = p_tenant_id), 3, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2320-GST-SGST-OUT' AND tenant_id = p_tenant_id), 'DEBIT', 'SGST_AMOUNT', 'SGST Reversal', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = p_tenant_id), 4, 'LIABILITY', (SELECT id FROM account_masters WHERE code = '2330-GST-IGST-OUT' AND tenant_id = p_tenant_id), 'DEBIT', 'IGST_AMOUNT', 'IGST Reversal', FALSE),
    (p_tenant_id, (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = p_tenant_id), 5, 'ASSET', (SELECT id FROM account_masters WHERE code = '1100-AR' AND tenant_id = p_tenant_id), 'CREDIT', 'NET_AMOUNT', 'Credit Note {{ref}}', TRUE);
    
    GET DIAGNOSTICS v_rules_count = ROW_COUNT;
    
    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Transaction templates reinitialized'::TEXT, v_templates_count, v_rules_count;
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::TEXT, 0::INTEGER, 0::INTEGER;
END;
$$ LANGUAGE plpgsql;
