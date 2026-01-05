-- =====================================================
-- 3. INSERT TRANSACTION TEMPLATES (Now Safe)
-- =====================================================
INSERT INTO transaction_templates (tenant_id, module_id, transaction_type, code, name, description)
VALUES
-- INVENTORY MODULE
(1, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'SALES_INVOICE',      'TT001', 'Sales Invoice Template',          'Template for customer sales invoices'),
(1, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'PURCHASE_INVOICE',    'TT002', 'Purchase Invoice Template',       'Template for vendor purchase invoices'),
(1, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'STOCK_ADJUSTMENT',    'TT003', 'Stock Adjustment Template',       'Template for inventory adjustments'),
(1, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'PRODUCT_WASTED',      'TT004', 'Product Wasted Template',         'Template for recording wasted/damaged items'),
(1, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'DEBIT_NOTE',          'TT008', 'Debit Note Template',             'Template for issuing debit note to supplier'),
(1, (SELECT id FROM module_master WHERE module_code = 'INVENTORY'), 'CREDIT_NOTE',         'TT009', 'Credit Note Template',            'Template for issuing credit note to customer'),

-- ACCOUNTING MODULE
(1, (SELECT id FROM module_master WHERE module_code = 'ACCOUNT'), 'SALES_PAYMENT',       'TT005', 'Sales Payment Template',          'Template for receiving customer payments'),
(1, (SELECT id FROM module_master WHERE module_code = 'ACCOUNT'), 'PURCHASE_PAYMENT',    'TT006', 'Purchase Payment Template',       'Template for making vendor payments'),

-- HEALTH MODULE
(1, (SELECT id FROM module_master WHERE module_code = 'HEALTH'),     'PATIENT_BILL',        'TT007', 'Patient Bill Template',           'Template for patient billing'),

-- HEALTH MODULE (Diagnostic Services)
(1, (SELECT id FROM module_master WHERE module_code = 'HEALTH'), 'DIAGNOSTIC_BILL',     'TT010', 'Diagnostic Bill Template',        'Template for diagnostic services billing')
ON CONFLICT (tenant_id, code) DO NOTHING;

-- =====================================================
-- 4. INSERT ALL TRANSACTION TEMPLATE RULES (Safe)
-- =====================================================

-- 1. SALES_INVOICE
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = 1), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = 'AR001'), 'CREDIT', 'NET_AMOUNT', 'Invoice {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = 1), 2, 'INCOME', (SELECT id FROM account_masters WHERE code = 'SALES001'), 'DEBIT', 'TAXABLE_AMOUNT', 'Sales: {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = 1), 3, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'CGST_PAY'), 'DEBIT', 'CGST_AMOUNT', 'CGST @{{cgst_rate}}% on {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = 1), 4, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'SGST_PAY'), 'DEBIT', 'SGST_AMOUNT', 'SGST @{{sgst_rate}}% on {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = 1), 5, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'IGST_PAY'), 'DEBIT', 'IGST_AMOUNT', 'IGST @{{igst_rate}}% on {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = 1), 6, 'INCOME', (SELECT id FROM account_masters WHERE code = 'DISC_GIVEN'), 'CREDIT', 'TOTAL_DISCOUNT', 'Discount Allowed', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = 1), 7, 'EXPENSE', (SELECT id FROM account_masters WHERE code = 'COMM_SALES'), 'DEBIT', 'AGENT_COMMISSION', 'Agent Commission @{{agent_commission_percent}}% - {{agent_name}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_INVOICE' AND tenant_id = 1), 8, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'AP001'), 'CREDIT', 'AGENT_COMMISSION', 'Payable to Agent {{agent_name}}', TRUE);

-- 2. PURCHASE_INVOICE
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = 1), 1, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'AP001'), 'DEBIT', 'NET_AMOUNT', 'Bill {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = 1), 2, 'EXPENSE', (SELECT id FROM account_masters WHERE code = 'PUREXP001'), 'CREDIT', 'TAXABLE_AMOUNT', 'Purchase: {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = 1), 3, 'ASSET', (SELECT id FROM account_masters WHERE code = 'CGST_REC'), 'CREDIT', 'CGST_AMOUNT', 'CGST Input @{{cgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = 1), 4, 'ASSET', (SELECT id FROM account_masters WHERE code = 'SGST_REC'), 'CREDIT', 'SGST_AMOUNT', 'SGST Input @{{sgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = 1), 5, 'ASSET', (SELECT id FROM account_masters WHERE code = 'IGST_REC'), 'CREDIT', 'IGST_AMOUNT', 'IGST Input @{{igst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_INVOICE' AND tenant_id = 1), 6, 'INCOME', (SELECT id FROM account_masters WHERE code = 'DISC_RECEIVED'), 'DEBIT', 'TOTAL_DISCOUNT', 'Discount Received', FALSE);

-- 3. STOCK_ADJUSTMENT
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE transaction_type = 'STOCK_ADJUSTMENT' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'STOCK_ADJUSTMENT' AND tenant_id = 1), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = 'INV001'), 'DEBIT', 'TOTAL_AMOUNT', 'Inventory Increase', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'STOCK_ADJUSTMENT' AND tenant_id = 1), 2, 'EXPENSE', (SELECT id FROM account_masters WHERE code = 'WASTE_LOSS'), 'CREDIT', 'TOTAL_AMOUNT', 'Adjustment Expense (if loss)', FALSE);

-- 4. PRODUCT_WASTED
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE transaction_type = 'PRODUCT_WASTED' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PRODUCT_WASTED' AND tenant_id = 1), 1, 'EXPENSE', (SELECT id FROM account_masters WHERE code = 'WASTE_LOSS'), 'DEBIT', 'TOTAL_AMOUNT', 'Waste / Scrap Loss', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PRODUCT_WASTED' AND tenant_id = 1), 2, 'ASSET', (SELECT id FROM account_masters WHERE code = 'INV001'), 'CREDIT', 'TOTAL_AMOUNT', 'Inventory Reduction', FALSE);

-- 5. SALES_PAYMENT
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_PAYMENT' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_PAYMENT' AND tenant_id = 1), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = 'BANK001'), 'DEBIT', 'TOTAL_AMOUNT_FCY', 'Payment {{ref}} in {{currency}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_PAYMENT' AND tenant_id = 1), 2, 'ASSET', (SELECT id FROM account_masters WHERE code = 'AR001'), 'CREDIT', 'TOTAL_AMOUNT_BASE', 'Customer Payment (Base)', TRUE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_PAYMENT' AND tenant_id = 1), 3, 'INCOME', (SELECT id FROM account_masters WHERE code = 'EXCH_GAIN'), 'DEBIT', 'EXCHANGE_DIFF', 'FX Gain on {{ref}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'SALES_PAYMENT' AND tenant_id = 1), 4, 'EXPENSE', (SELECT id FROM account_masters WHERE code = 'EXCH_LOSS'), 'CREDIT', 'EXCHANGE_DIFF', 'FX Loss on {{ref}}', FALSE);

-- 6. PURCHASE_PAYMENT
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_PAYMENT' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_PAYMENT' AND tenant_id = 1), 1, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'AP001'), 'DEBIT', 'TOTAL_AMOUNT_BASE', 'Vendor Payment (Base)', TRUE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_PAYMENT' AND tenant_id = 1), 2, 'ASSET', (SELECT id FROM account_masters WHERE code = 'BANK001'), 'CREDIT', 'TOTAL_AMOUNT_FCY', 'Payment {{ref}} in {{currency}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_PAYMENT' AND tenant_id = 1), 3, 'INCOME', (SELECT id FROM account_masters WHERE code = 'EXCH_GAIN'), 'DEBIT', 'EXCHANGE_DIFF', 'FX Gain on {{ref}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PURCHASE_PAYMENT' AND tenant_id = 1), 4, 'EXPENSE', (SELECT id FROM account_masters WHERE code = 'EXCH_LOSS'), 'CREDIT', 'EXCHANGE_DIFF', 'FX Loss on {{ref}}', FALSE);

-- 7. PATIENT_BILL
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = 1), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = 'AR001'), 'CREDIT', 'NET_AMOUNT', 'Patient Bill {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = 1), 2, 'INCOME', (SELECT id FROM account_masters WHERE code = 'CLINI001'), 'DEBIT', 'TAXABLE_AMOUNT', 'Clinic Revenue: {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = 1), 3, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'CGST_PAY'), 'DEBIT', 'CGST_AMOUNT', 'CGST @{{cgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = 1), 4, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'SGST_PAY'), 'DEBIT', 'SGST_AMOUNT', 'SGST @{{sgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = 1), 5, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'IGST_PAY'), 'DEBIT', 'IGST_AMOUNT', 'IGST @{{igst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = 1), 6, 'INCOME', (SELECT id FROM account_masters WHERE code = 'DISC_GIVEN'), 'CREDIT', 'TOTAL_DISCOUNT', 'Discount Allowed', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = 1), 7, 'EXPENSE', (SELECT id FROM account_masters WHERE code = 'COMM_CLINIC'), 'DEBIT', 'AGENT_COMMISSION', 'Clinic Agent Commission @{{agent_commission_percent}}% - {{agent_name}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'PATIENT_BILL' AND tenant_id = 1), 8, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'AP001'), 'CREDIT', 'AGENT_COMMISSION', 'Payable to Agent {{agent_name}}', TRUE);

-- 8. DEBIT_NOTE
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = 1), 1, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'AP001'), 'CREDIT', 'NET_AMOUNT', 'Debit Note {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = 1), 2, 'EXPENSE', (SELECT id FROM account_masters WHERE code = 'PURCHASE_RET'), 'DEBIT', 'TAXABLE_AMOUNT', 'Purchase Return', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = 1), 3, 'ASSET', (SELECT id FROM account_masters WHERE code = 'CGST_REC'), 'DEBIT', 'CGST_AMOUNT', 'CGST Reversal', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = 1), 4, 'ASSET', (SELECT id FROM account_masters WHERE code = 'SGST_REC'), 'DEBIT', 'SGST_AMOUNT', 'SGST Reversal', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DEBIT_NOTE' AND tenant_id = 1), 5, 'ASSET', (SELECT id FROM account_masters WHERE code = 'IGST_REC'), 'DEBIT', 'IGST_AMOUNT', 'IGST Reversal', FALSE);

-- 9. CREDIT_NOTE
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = 1), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = 'AR001'), 'DEBIT', 'NET_AMOUNT', 'Credit Note {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = 1), 2, 'INCOME', (SELECT id FROM account_masters WHERE code = 'SALES_RET'), 'CREDIT', 'TAXABLE_AMOUNT', 'Sales Return', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = 1), 3, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'CGST_PAY'), 'CREDIT', 'CGST_AMOUNT', 'CGST Reversal', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = 1), 4, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'SGST_PAY'), 'CREDIT', 'SGST_AMOUNT', 'SGST Reversal', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'CREDIT_NOTE' AND tenant_id = 1), 5, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'IGST_PAY'), 'CREDIT', 'IGST_AMOUNT', 'IGST Reversal', FALSE);

-- 10. DIAGNOSTIC_BILL
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = 1), 1, 'ASSET', (SELECT id FROM account_masters WHERE code = 'AR001'), 'CREDIT', 'NET_AMOUNT', 'Diagnostic Bill {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = 1), 2, 'INCOME', (SELECT id FROM account_masters WHERE code = 'DIAGN001'), 'DEBIT', 'TAXABLE_AMOUNT', 'Diagnostic Revenue: {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = 1), 3, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'CGST_PAY'), 'DEBIT', 'CGST_AMOUNT', 'CGST @{{cgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = 1), 4, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'SGST_PAY'), 'DEBIT', 'SGST_AMOUNT', 'SGST @{{sgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = 1), 5, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'IGST_PAY'), 'DEBIT', 'IGST_AMOUNT', 'IGST @{{igst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = 1), 6, 'INCOME', (SELECT id FROM account_masters WHERE code = 'DISC_GIVEN'), 'CREDIT', 'TOTAL_DISCOUNT', 'Discount Allowed', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = 1), 7, 'EXPENSE', (SELECT id FROM account_masters WHERE code = 'COMM_DIAGN'), 'DEBIT', 'AGENT_COMMISSION', 'Diagnostic Agent Commission @{{agent_commission_percent}}% - {{agent_name}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE transaction_type = 'DIAGNOSTIC_BILL' AND tenant_id = 1), 8, 'LIABILITY', (SELECT id FROM account_masters WHERE code = 'AP001'), 'CREDIT', 'AGENT_COMMISSION', 'Payable to Agent {{agent_name}}', TRUE);