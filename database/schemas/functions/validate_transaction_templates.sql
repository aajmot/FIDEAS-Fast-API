CREATE OR REPLACE FUNCTION validate_transaction_templates(p_tenant_id INT)
RETURNS TABLE(issue TEXT, template_code TEXT, detail TEXT) AS $$
BEGIN

    -- =====================================================
    -- 1. MISSING ACCOUNT
    -- =====================================================
    RETURN QUERY
    SELECT 
        'MISSING ACCOUNT'::TEXT AS issue,
        tt.code AS template_code,
        CONCAT('Account ID: ', r.account_id, ' (Code not found)')::TEXT AS detail
    FROM transaction_template_rules r
    JOIN transaction_templates tt ON r.template_id = tt.id AND tt.tenant_id = p_tenant_id
    LEFT JOIN chart_of_accounts ca ON r.account_id = ca.id AND ca.tenant_id = p_tenant_id
    WHERE r.tenant_id = p_tenant_id AND ca.id IS NULL;

    -- =====================================================
    -- 2. MISSING TEMPLATE
    -- =====================================================
    RETURN QUERY
    SELECT 
        'MISSING TEMPLATE'::TEXT AS issue,
        'N/A'::TEXT AS template_code,
        CONCAT('Rule ID: ', r.id, ', Line: ', r.line_number)::TEXT AS detail
    FROM transaction_template_rules r
    LEFT JOIN transaction_templates tt ON r.template_id = tt.id AND tt.tenant_id = p_tenant_id
    WHERE r.tenant_id = p_tenant_id AND tt.id IS NULL;

    -- =====================================================
    -- 3. MISSING MODULE
    -- =====================================================
    RETURN QUERY
    SELECT 
        'MISSING MODULE'::TEXT AS issue,
        tt.code AS template_code,
        CONCAT('Module ID: ', tt.module_id)::TEXT AS detail
    FROM transaction_templates tt
    LEFT JOIN module_master mm ON tt.module_id = mm.id
    WHERE tt.tenant_id = p_tenant_id AND mm.id IS NULL;

    -- =====================================================
    -- 4. DOUBLE-ENTRY BALANCE (Enhanced for GST + Discount + FX)
    -- =====================================================
    WITH amounts AS (
        SELECT 
            tt.code AS template_code,
            r.entry_type,
            r.amount_source,
            CASE 
                WHEN r.amount_source = 'NET_AMOUNT'      THEN 118.00  -- taxable + tax
                WHEN r.amount_source = 'TAXABLE_AMOUNT'  THEN 100.00
                WHEN r.amount_source = 'TOTAL_AMOUNT'    THEN 118.00  -- legacy
                WHEN r.amount_source = 'TOTAL_TAX'       THEN 18.00   -- legacy
                WHEN r.amount_source = 'CGST_AMOUNT'     THEN 9.00
                WHEN r.amount_source = 'SGST_AMOUNT'     THEN 9.00
                WHEN r.amount_source = 'IGST_AMOUNT'     THEN 18.00
                WHEN r.amount_source = 'TOTAL_DISCOUNT'  THEN 5.00
                WHEN r.amount_source = 'TOTAL_AMOUNT_FCY' THEN 120.00
                WHEN r.amount_source = 'TOTAL_AMOUNT_BASE' THEN 118.00
                WHEN r.amount_source = 'EXCHANGE_DIFF'   THEN 2.00
                ELSE 0.00
            END AS test_amount,
            CASE WHEN r.entry_type = 'DEBIT' THEN 1 ELSE -1 END AS sign
        FROM transaction_template_rules r
        JOIN transaction_templates tt ON r.template_id = tt.id
        WHERE r.tenant_id = p_tenant_id AND tt.tenant_id = p_tenant_id
    ),
    balance AS (
        SELECT 
            template_code,
            SUM(test_amount * sign) AS net_balance
        FROM amounts
        GROUP BY template_code
        HAVING ABS(SUM(test_amount * sign)) > 0.01  -- allow rounding
    )
    RETURN QUERY
    SELECT 
        'IMBALANCED TEMPLATE'::TEXT AS issue,
        template_code,
        CONCAT('Net: ', net_balance::TEXT)::TEXT AS detail
    FROM balance;

    -- =====================================================
    -- 5. INVALID SUBLEDGER (only AR/AP)
    -- =====================================================
    RETURN QUERY
    SELECT 
        'INVALID SUBLEDGER'::TEXT AS issue,
        tt.code AS template_code,
        CONCAT('Account: ', ca.account_code, ', Line: ', r.line_number)::TEXT AS detail
    FROM transaction_template_rules r
    JOIN transaction_templates tt ON r.template_id = tt.id
    JOIN chart_of_accounts ca ON r.account_id = ca.id
    WHERE r.tenant_id = p_tenant_id
      AND ca.tenant_id = p_tenant_id
      AND r.is_sub_ledger = TRUE
      AND ca.account_code NOT IN ('AR001', 'AP001');

    -- =====================================================
    -- 6. INVALID AMOUNT_SOURCE
    -- =====================================================
    RETURN QUERY
    SELECT 
        'INVALID AMOUNT_SOURCE'::TEXT AS issue,
        tt.code AS template_code,
        CONCAT(r.amount_source, ' (Line: ', r.line_number, ')')::TEXT AS detail
    FROM transaction_template_rules r
    JOIN transaction_templates tt ON r.template_id = tt.id
    WHERE r.tenant_id = p_tenant_id
      AND tt.tenant_id = p_tenant_id
      AND r.amount_source NOT IN (
          'NET_AMOUNT', 'TAXABLE_AMOUNT', 'TOTAL_AMOUNT', 'TOTAL_TAX',
          'CGST_AMOUNT', 'SGST_AMOUNT', 'IGST_AMOUNT',
          'TOTAL_DISCOUNT',
          'TOTAL_AMOUNT_FCY', 'TOTAL_AMOUNT_BASE', 'EXCHANGE_DIFF'
      );

    -- =====================================================
    -- 7. ACCOUNT TYPE MISMATCH (Critical!)
    -- =====================================================
    RETURN QUERY
    SELECT 
        'WRONG ACCOUNT TYPE'::TEXT AS issue,
        tt.code AS template_code,
        CONCAT('Account: ', ca.account_code, ' | Expected: ', 
               CASE 
                   WHEN ca.account_code LIKE 'AR%' THEN 'ASSET'
                   WHEN ca.account_code LIKE 'AP%' THEN 'LIABILITY'
                   WHEN ca.account_code IN ('CGST_PAY','SGST_PAY','IGST_PAY') THEN 'LIABILITY'
                   WHEN ca.account_code IN ('CGST_REC','SGST_REC','IGST_REC') THEN 'ASSET'
                   WHEN ca.account_code IN ('SALES001','CLINI001') THEN 'INCOME'
                   WHEN ca.account_code IN ('PUREXP001','WASTE_LOSS') THEN 'EXPENSE'
                   ELSE 'UNKNOWN'
               END,
               ' | Found: ', r.account_type
        )::TEXT AS detail
    FROM transaction_template_rules r
    JOIN transaction_templates tt ON r.template_id = tt.id
    JOIN chart_of_accounts ca ON r.account_id = ca.id
    WHERE r.tenant_id = p_tenant_id
      AND ca.tenant_id = p_tenant_id
      AND (
          (ca.account_code LIKE 'AR%' AND r.account_type != 'ASSET') OR
          (ca.account_code LIKE 'AP%' AND r.account_type != 'LIABILITY') OR
          (ca.account_code IN ('CGST_PAY','SGST_PAY','IGST_PAY') AND r.account_type != 'LIABILITY') OR
          (ca.account_code IN ('CGST_REC','SGST_REC','IGST_REC') AND r.account_type != 'ASSET') OR
          (ca.account_code IN ('SALES001','CLINI001','SALES_RET') AND r.account_type != 'INCOME') OR
          (ca.account_code IN ('PUREXP001','WASTE_LOSS','PURCHASE_RET') AND r.account_type != 'EXPENSE')
      );

    -- =====================================================
    -- 8. FINAL: ALL GOOD?
    -- =====================================================
    IF NOT EXISTS (
        SELECT 1 FROM (
            SELECT 1 FROM transaction_template_rules r
            LEFT JOIN chart_of_accounts ca ON r.account_id = ca.id AND ca.tenant_id = p_tenant_id
            LEFT JOIN transaction_templates tt ON r.template_id = tt.id AND tt.tenant_id = p_tenant_id
            LEFT JOIN module_master mm ON tt.module_id = mm.id
            WHERE r.tenant_id = p_tenant_id
              AND (ca.id IS NULL OR tt.id IS NULL OR mm.id IS NULL)
            UNION ALL
            SELECT 1 FROM balance
            UNION ALL
            SELECT 1 FROM transaction_template_rules r
            JOIN transaction_templates tt ON r.template_id = tt.id
            JOIN chart_of_accounts ca ON r.account_id = ca.id
            WHERE r.is_sub_ledger = TRUE AND ca.account_code NOT IN ('AR001', 'AP001')
            UNION ALL
            SELECT 1 FROM transaction_template_rules r
            JOIN transaction_templates tt ON r.template_id = tt.id
            WHERE r.amount_source NOT IN (
                'NET_AMOUNT','TAXABLE_AMOUNT','TOTAL_AMOUNT','TOTAL_TAX',
                'CGST_AMOUNT','SGST_AMOUNT','IGST_AMOUNT',
                'TOTAL_DISCOUNT','TOTAL_AMOUNT_FCY','TOTAL_AMOUNT_BASE','EXCHANGE_DIFF'
            )
            UNION ALL
            SELECT 1 FROM transaction_template_rules r
            JOIN transaction_templates tt ON r.template_id = tt.id
            JOIN chart_of_accounts ca ON r.account_id = ca.id
            WHERE (
                (ca.account_code LIKE 'AR%' AND r.account_type != 'ASSET') OR
                (ca.account_code LIKE 'AP%' AND r.account_type != 'LIABILITY') OR
                (ca.account_code IN ('CGST_PAY','SGST_PAY','IGST_PAY') AND r.account_type != 'LIABILITY') OR
                (ca.account_code IN ('CGST_REC','SGST_REC','IGST_REC') AND r.account_type != 'ASSET')
            )
        ) AS errors
    ) THEN
        RETURN QUERY SELECT 'VALIDATION PASSED'::TEXT, 'ALL'::TEXT, 'All checks cleared!'::TEXT;
    END IF;

END;
$$ LANGUAGE plpgsql;