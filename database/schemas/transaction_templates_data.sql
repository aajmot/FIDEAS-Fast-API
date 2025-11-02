-- =====================================================
-- COMPLETE TRANSACTION TEMPLATES (All Modules)
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
(1, (SELECT id FROM module_master WHERE module_code = 'ACCOUNTING'), 'SALES_PAYMENT',       'TT005', 'Sales Payment Template',          'Template for receiving customer payments'),
(1, (SELECT id FROM module_master WHERE module_code = 'ACCOUNTING'), 'PURCHASE_PAYMENT',    'TT006', 'Purchase Payment Template',       'Template for making vendor payments'),

-- CLINIC MODULE
(1, (SELECT id FROM module_master WHERE module_code = 'CLINIC'),     'PATIENT_BILL',        'TT007', 'Patient Bill Template',           'Template for patient billing'),

-- DIAGNOSTIC MODULE (Added for completeness; adjust module_code if needed)
(1, (SELECT id FROM module_master WHERE module_code = 'DIAGNOSTIC'), 'DIAGNOSTIC_BILL',     'TT010', 'Diagnostic Bill Template',        'Template for diagnostic services billing');

-- =====================================================
-- COMPLETE TRANSACTION TEMPLATE RULES (All Templates)
-- Supports: GST Split, Discounts, Multi-Currency, Auto-Narration, Agent Commission
-- =====================================================

-- 1. SALES_INVOICE (With Agent Commission)
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE code = 'SALES_INVOICE' AND tenant_id = 1);
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_INVOICE'), 1, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'AR001'), 'CREDIT', 'NET_AMOUNT', 'Invoice {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_INVOICE'), 2, 'INCOME', (SELECT id FROM chart_of_accounts WHERE account_code = 'SALES001'), 'DEBIT', 'TAXABLE_AMOUNT', 'Sales: {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_INVOICE'), 3, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'CGST_PAY'), 'DEBIT', 'CGST_AMOUNT', 'CGST @{{cgst_rate}}% on {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_INVOICE'), 4, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'SGST_PAY'), 'DEBIT', 'SGST_AMOUNT', 'SGST @{{sgst_rate}}% on {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_INVOICE'), 5, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'IGST_PAY'), 'DEBIT', 'IGST_AMOUNT', 'IGST @{{igst_rate}}% on {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_INVOICE'), 6, 'INCOME', (SELECT id FROM chart_of_accounts WHERE account_code = 'DISC_GIVEN'), 'CREDIT', 'TOTAL_DISCOUNT', 'Discount Allowed', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_INVOICE'), 7, 'EXPENSE', (SELECT id FROM chart_of_accounts WHERE account_code = 'COMM_SALES'), 'DEBIT', 'AGENT_COMMISSION', 'Agent Commission @{{agent_commission_percent}}% - {{agent_name}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_INVOICE'), 8, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'AP001'), 'CREDIT', 'AGENT_COMMISSION', 'Payable to Agent {{agent_name}}', TRUE);

-- 2. PURCHASE_INVOICE
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_INVOICE');
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_INVOICE'), 1, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'AP001'), 'DEBIT', 'NET_AMOUNT', 'Bill {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_INVOICE'), 2, 'EXPENSE', (SELECT id FROM chart_of_accounts WHERE account_code = 'PUREXP001'), 'CREDIT', 'TAXABLE_AMOUNT', 'Purchase: {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_INVOICE'), 3, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'CGST_REC'), 'CREDIT', 'CGST_AMOUNT', 'CGST Input @{{cgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_INVOICE'), 4, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'SGST_REC'), 'CREDIT', 'SGST_AMOUNT', 'SGST Input @{{sgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_INVOICE'), 5, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'IGST_REC'), 'CREDIT', 'IGST_AMOUNT', 'IGST Input @{{igst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_INVOICE'), 6, 'INCOME', (SELECT id FROM chart_of_accounts WHERE account_code = 'DISC_RECEIVED'), 'DEBIT', 'TOTAL_DISCOUNT', 'Discount Received', FALSE);

-- 3. STOCK_ADJUSTMENT
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE code = 'STOCK_ADJUSTMENT');
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE code = 'STOCK_ADJUSTMENT'), 1, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'INV001'), 'DEBIT', 'TOTAL_AMOUNT', 'Inventory Increase', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'STOCK_ADJUSTMENT'), 2, 'EXPENSE', (SELECT id FROM chart_of_accounts WHERE account_code = 'WASTE_LOSS'), 'CREDIT', 'TOTAL_AMOUNT', 'Adjustment Expense (if loss)', FALSE);

-- 4. PRODUCT_WASTED
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE code = 'PRODUCT_WASTED');
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE code = 'PRODUCT_WASTED'), 1, 'EXPENSE', (SELECT id FROM chart_of_accounts WHERE account_code = 'WASTE_LOSS'), 'DEBIT', 'TOTAL_AMOUNT', 'Waste / Scrap Loss', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PRODUCT_WASTED'), 2, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'INV001'), 'CREDIT', 'TOTAL_AMOUNT', 'Inventory Reduction', FALSE);

-- 5. SALES_PAYMENT
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE code = 'SALES_PAYMENT');
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_PAYMENT'), 1, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'BANK001'), 'DEBIT', 'TOTAL_AMOUNT_FCY', 'Payment {{ref}} in {{currency}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_PAYMENT'), 2, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'AR001'), 'CREDIT', 'TOTAL_AMOUNT_BASE', 'Customer Payment (Base)', TRUE),
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_PAYMENT'), 3, 'INCOME', (SELECT id FROM chart_of_accounts WHERE account_code = 'EXCH_GAIN'), 'DEBIT', 'EXCHANGE_DIFF', 'FX Gain on {{ref}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'SALES_PAYMENT'), 4, 'EXPENSE', (SELECT id FROM chart_of_accounts WHERE account_code = 'EXCH_LOSS'), 'CREDIT', 'EXCHANGE_DIFF', 'FX Loss on {{ref}}', FALSE);

-- 6. PURCHASE_PAYMENT
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_PAYMENT');
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_PAYMENT'), 1, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'AP001'), 'DEBIT', 'TOTAL_AMOUNT_BASE', 'Vendor Payment (Base)', TRUE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_PAYMENT'), 2, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'BANK001'), 'CREDIT', 'TOTAL_AMOUNT_FCY', 'Payment {{ref}} in {{currency}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_PAYMENT'), 3, 'INCOME', (SELECT id FROM chart_of_accounts WHERE account_code = 'EXCH_GAIN'), 'DEBIT', 'EXCHANGE_DIFF', 'FX Gain on {{ref}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PURCHASE_PAYMENT'), 4, 'EXPENSE', (SELECT id FROM chart_of_accounts WHERE account_code = 'EXCH_LOSS'), 'CREDIT', 'EXCHANGE_DIFF', 'FX Loss on {{ref}}', FALSE);

-- 7. PATIENT_BILL (With Agent Commission)
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE code = 'PATIENT_BILL');
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE code = 'PATIENT_BILL'), 1, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'AR001'), 'CREDIT', 'NET_AMOUNT', 'Patient Bill {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PATIENT_BILL'), 2, 'INCOME', (SELECT id FROM chart_of_accounts WHERE account_code = 'CLINI001'), 'DEBIT', 'TAXABLE_AMOUNT', 'Clinic Revenue: {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PATIENT_BILL'), 3, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'CGST_PAY'), 'DEBIT', 'CGST_AMOUNT', 'CGST @{{cgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PATIENT_BILL'), 4, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'SGST_PAY'), 'DEBIT', 'SGST_AMOUNT', 'SGST @{{sgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PATIENT_BILL'), 5, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'IGST_PAY'), 'DEBIT', 'IGST_AMOUNT', 'IGST @{{igst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PATIENT_BILL'), 6, 'INCOME', (SELECT id FROM chart_of_accounts WHERE account_code = 'DISC_GIVEN'), 'CREDIT', 'TOTAL_DISCOUNT', 'Discount Allowed', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PATIENT_BILL'), 7, 'EXPENSE', (SELECT id FROM chart_of_accounts WHERE account_code = 'COMM_CLINIC'), 'DEBIT', 'AGENT_COMMISSION', 'Clinic Agent Commission @{{agent_commission_percent}}% - {{agent_name}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'PATIENT_BILL'), 8, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'AP001'), 'CREDIT', 'AGENT_COMMISSION', 'Payable to Agent {{agent_name}}', TRUE);

-- 8. DEBIT_NOTE
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE code = 'DEBIT_NOTE');
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE code = 'DEBIT_NOTE'), 1, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'AP001'), 'CREDIT', 'NET_AMOUNT', 'Debit Note {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DEBIT_NOTE'), 2, 'EXPENSE', (SELECT id FROM chart_of_accounts WHERE account_code = 'PURCHASE_RET'), 'DEBIT', 'TAXABLE_AMOUNT', 'Purchase Return', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DEBIT_NOTE'), 3, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'CGST_REC'), 'DEBIT', 'CGST_AMOUNT', 'CGST Reversal', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DEBIT_NOTE'), 4, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'SGST_REC'), 'DEBIT', 'SGST_AMOUNT', 'SGST Reversal', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DEBIT_NOTE'), 5, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'IGST_REC'), 'DEBIT', 'IGST_AMOUNT', 'IGST Reversal', FALSE);

-- 9. CREDIT_NOTE
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE code = 'CREDIT_NOTE');
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE code = 'CREDIT_NOTE'), 1, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'AR001'), 'DEBIT', 'NET_AMOUNT', 'Credit Note {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE code = 'CREDIT_NOTE'), 2, 'INCOME', (SELECT id FROM chart_of_accounts WHERE account_code = 'SALES_RET'), 'CREDIT', 'TAXABLE_AMOUNT', 'Sales Return', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'CREDIT_NOTE'), 3, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'CGST_PAY'), 'CREDIT', 'CGST_AMOUNT', 'CGST Reversal', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'CREDIT_NOTE'), 4, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'SGST_PAY'), 'CREDIT', 'SGST_AMOUNT', 'SGST Reversal', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'CREDIT_NOTE'), 5, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'IGST_PAY'), 'CREDIT', 'IGST_AMOUNT', 'IGST Reversal', FALSE);

-- 10. DIAGNOSTIC_BILL (With Agent Commission)
DELETE FROM transaction_template_rules WHERE template_id = (SELECT id FROM transaction_templates WHERE code = 'DIAGNOSTIC_BILL');
INSERT INTO transaction_template_rules (tenant_id, template_id, line_number, account_type, account_id, entry_type, amount_source, narration, is_sub_ledger)
VALUES
(1, (SELECT id FROM transaction_templates WHERE code = 'DIAGNOSTIC_BILL'), 1, 'ASSET', (SELECT id FROM chart_of_accounts WHERE account_code = 'AR001'), 'CREDIT', 'NET_AMOUNT', 'Diagnostic Bill {{ref}} | {{line_items}}', TRUE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DIAGNOSTIC_BILL'), 2, 'INCOME', (SELECT id FROM chart_of_accounts WHERE account_code = 'DIAGN001'), 'DEBIT', 'TAXABLE_AMOUNT', 'Diagnostic Revenue: {{line_items}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DIAGNOSTIC_BILL'), 3, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'CGST_PAY'), 'DEBIT', 'CGST_AMOUNT', 'CGST @{{cgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DIAGNOSTIC_BILL'), 4, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'SGST_PAY'), 'DEBIT', 'SGST_AMOUNT', 'SGST @{{sgst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DIAGNOSTIC_BILL'), 5, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'IGST_PAY'), 'DEBIT', 'IGST_AMOUNT', 'IGST @{{igst_rate}}%', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DIAGNOSTIC_BILL'), 6, 'INCOME', (SELECT id FROM chart_of_accounts WHERE account_code = 'DISC_GIVEN'), 'CREDIT', 'TOTAL_DISCOUNT', 'Discount Allowed', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DIAGNOSTIC_BILL'), 7, 'EXPENSE', (SELECT id FROM chart_of_accounts WHERE account_code = 'COMM_DIAGN'), 'DEBIT', 'AGENT_COMMISSION', 'Diagnostic Agent Commission @{{agent_commission_percent}}% - {{agent_name}}', FALSE),
(1, (SELECT id FROM transaction_templates WHERE code = 'DIAGNOSTIC_BILL'), 8, 'LIABILITY', (SELECT id FROM chart_of_accounts WHERE account_code = 'AP001'), 'CREDIT', 'AGENT_COMMISSION', 'Payable to Agent {{agent_name}}', TRUE);