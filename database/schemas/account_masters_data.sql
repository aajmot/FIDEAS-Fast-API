-- === account_masters (enhanced) ===
INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, opening_balance, current_balance, is_system_assigned) 
VALUES
-- ASSETS
(1, (SELECT id FROM account_groups WHERE code='ASET'), 'CASH001', 'Cash Account', 'Main cash account', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='ASET'), 'BANK001', 'Bank Account', 'Main bank account', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='ASET'), 'AR001', 'Account Receivable', 'Customer receivables', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='ASET'), 'INV001', 'Inventory Account', 'Inventory asset', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='ASET'), 'CGST_REC', 'CGST Input Credit', 'CGST recoverable', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='ASET'), 'SGST_REC', 'SGST Input Credit', 'SGST recoverable', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='ASET'), 'IGST_REC', 'IGST Input Credit', 'IGST recoverable', 0,0,TRUE),

-- LIABILITIES
(1, (SELECT id FROM account_groups WHERE code='LIAB'), 'AP001', 'Account Payable', 'Vendor payables', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='LIAB'), 'CGST_PAY', 'CGST Payable', 'CGST output tax', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='LIAB'), 'SGST_PAY', 'SGST Payable', 'SGST output tax', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='LIAB'), 'IGST_PAY', 'IGST Payable', 'IGST output tax', 0,0,TRUE),

-- EQUITY
(1, (SELECT id FROM account_groups WHERE code='EQTY'), 'OE001', 'Owner Equity', 'Owner capital', 0,0,TRUE),

-- INCOME
(1, (SELECT id FROM account_groups WHERE code='INCM'), 'SALES001', 'Sales Revenue', 'Product sales', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='INCM'), 'CLINI001', 'Clinic Revenue', 'Clinic services', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='INCM'), 'DIAGN001', 'Diagnostic Revenue', 'Diagnostic services', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='INCM'), 'SALES_RET', 'Sales Returns', 'Sales returns/allowances', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='INCM'), 'EXCH_GAIN', 'Exchange Gain', 'FX gain', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='INCM'), 'DISC_GIVEN', 'Discount Allowed', 'Customer discounts', 0,0,TRUE),

-- EXPENSE
(1, (SELECT id FROM account_groups WHERE code='EXPN'), 'GNEXP001', 'General Expense', 'Misc expense', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='EXPN'), 'OPEXP001', 'Operating Expense', 'Operating costs', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='EXPN'), 'PUREXP001', 'Purchase Expense', 'Cost of purchase', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='EXPN'), 'PURCHASE_RET', 'Purchase Returns', 'Purchase returns', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='EXPN'), 'WASTE_LOSS', 'Waste Loss', 'Inventory write-off', 0,0,TRUE),
(1, (SELECT id FROM account_groups WHERE code='EXPN'), 'EXCH_LOSS', 'Exchange Loss', 'FX loss', 0,0,TRUE);

-- === EXPENSE: Agent Commission Accounts ===
INSERT INTO account_masters (tenant_id, account_group_id, code, name, description, opening_balance, current_balance, is_system_assigned)
VALUES
-- 1. Product Sales Agent Commission
(1, (SELECT id FROM account_groups WHERE code='EXPN'), 'COMM_SALES', 'Agent Commission - Sales', 'Commission paid to agents on product sales', 0, 0, TRUE),

-- 2. Clinic Agent Commission
(1, (SELECT id FROM account_groups WHERE code='EXPN'), 'COMM_CLINIC', 'Agent Commission - Clinic', 'Commission paid to agents on clinic services', 0, 0, TRUE),

-- 3. Diagnostic Agent Commission
(1, (SELECT id FROM account_groups WHERE code='EXPN'), 'COMM_DIAGN', 'Agent Commission - Diagnostics', 'Commission paid to agents on diagnostic services', 0, 0, TRUE);