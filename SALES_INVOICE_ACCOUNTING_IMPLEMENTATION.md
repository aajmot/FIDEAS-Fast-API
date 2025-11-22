# Sales Invoice Accounting & Stock Implementation Summary

## Overview
Extended sales invoice functionality to include:
1. Automatic customer account creation in chart of accounts
2. Proper double-entry accounting vouchers for invoice and payment
3. Stock transaction tracking for inventory management
4. Full integration with GST tax system (CGST, SGST, IGST, UGST, CESS)

## Implementation Details

### 1. Customer Account Auto-Creation
**File**: `modules/inventory_module/services/sales_invoice_service.py`
**Method**: `_get_or_create_customer_account()`

**Features**:
- Creates unique customer accounts with code format: `AR-{customer_id:06d}` (e.g., `AR-000001`)
- Account Type: `ASSET` (Accounts Receivable)
- Normal Balance: `DEBIT`
- Links to configured Accounts Receivable group with multiple fallback strategies:
  1. Uses tenant-configured `ACCOUNTS_RECEIVABLE` account setting
  2. Falls back to AccountGroup with code `ACCOUNTS_RECEIVABLE`
  3. Falls back to any ASSET type account group
  4. Raises error if no suitable group found
- Handles duplicate account codes by appending timestamp
- Auto-activates and sets as sub-ledger account

**Accounting Logic**:
- Customer accounts are ASSET accounts (debit increases receivable, credit decreases)
- Reflects amounts owed by customers to the company

### 2. Sales Invoice Voucher Creation
**File**: `modules/inventory_module/services/sales_invoice_service.py`
**Method**: `_create_sales_voucher()`

**Voucher Entries** (Double-Entry Bookkeeping):
```
Dr: Customer Receivable Account (ASSET)    = Total Invoice Amount
Cr: Sales Revenue Account (INCOME)         = Base Amount
Cr: CGST Output Account (LIABILITY)        = CGST Amount (if applicable)
Cr: SGST Output Account (LIABILITY)        = SGST Amount (if applicable)
Cr: IGST Output Account (LIABILITY)        = IGST Amount (if applicable)
Cr: UGST Output Account (LIABILITY)        = UGST Amount (if applicable)
Cr: CESS Output Account (LIABILITY)        = CESS Amount (if applicable)
```

**Features**:
- Creates SALES voucher type with auto-generated voucher number
- Records both base currency and foreign currency amounts
- Links voucher to invoice via reference_type='INVOICE' and reference_id
- Handles all GST tax types with separate output accounts
- Updates invoice with voucher_id after creation

**Tax Account Configuration Required**:
- `SALES_ACCOUNT` - Revenue/Income account
- `CGST_OUTPUT_ACCOUNT` - CGST Payable
- `SGST_OUTPUT_ACCOUNT` - SGST Payable
- `IGST_OUTPUT_ACCOUNT` - IGST Payable
- `UGST_OUTPUT_ACCOUNT` - UGST Payable (optional)
- `CESS_OUTPUT_ACCOUNT` - CESS Payable (optional)

### 3. Payment Receipt Voucher Creation
**File**: `modules/inventory_module/services/sales_invoice_service.py`
**Methods**: `_create_payment()`, `_create_payment_voucher()`

**Voucher Entries**:
```
Dr: Bank/Cash Account (ASSET)              = Payment Amount (per payment mode)
Cr: Customer Receivable Account (ASSET)    = Total Payment Amount
```

**Features**:
- Creates RECEIPT voucher type with voucher number `REC-{payment_number}`
- Supports multiple payment modes: CASH, BANK, CARD, UPI, CHEQUE, ONLINE, WALLET
- Each payment detail line creates separate debit entry
- Single credit entry to customer account for total payment
- Automatically uses payment detail's specified account_id or bank_account_id
- Falls back to configured CASH/BANK accounts if not specified
- Links payment to voucher via payment.voucher_id
- Handles multi-currency with exchange rates

**Payment Account Configuration Required**:
- `CASH` - Default cash account
- `BANK` - Default bank account
- Or specific bank accounts assigned per payment detail

### 4. Stock Transaction Recording
**File**: `modules/inventory_module/services/stock_service.py`
**Methods**: `record_sales_invoice_transaction_in_session()`, `reverse_sales_invoice_transaction_in_session()`

**Stock OUT Transaction** (on invoice create):
- Transaction Type: `OUT`
- Transaction Source: `SALES_INVOICE`
- Records quantity and unit price for each invoice line item
- Updates StockBalance:
  - Decreases total_quantity
  - Decreases available_quantity
  - Maintains average_cost (no change on sales)
- Supports batch number tracking

**Stock Reversal** (on invoice update/delete):
- Transaction Type: `IN` (reverses OUT)
- Transaction Source: `SALES_INVOICE_REVERSAL`
- Reference Number: `REV-{invoice_number}`
- Restores stock quantities by recording IN transaction
- Automatically called before deleting items on update
- Automatically called on invoice delete

**Integration Points**:
- **Create**: Stock OUT recorded after items are flushed in `create()` method
- **Update**: Stock reversal → delete old items → create new items → record new stock OUT
- **Delete**: Stock reversal before soft-deleting invoice

### 5. Complete Flow Example

**Creating Sales Invoice with Payment**:
1. Invoice created with customer, items, taxes
2. Items flushed to get IDs
3. **Stock Service**: Records OUT transactions for each item
4. **Accounting**: Creates SALES voucher (Dr: Customer, Cr: Sales+Taxes)
5. Invoice linked to voucher
6. **Payment**: Creates payment record
7. **Payment Details**: Creates detail records (bank, cash, etc.)
8. **Accounting**: Creates RECEIPT voucher (Dr: Bank/Cash, Cr: Customer)
9. Payment linked to voucher

**Updating Sales Invoice**:
1. Validates invoice is in DRAFT status
2. **Stock Service**: Reverses existing OUT transactions
3. Deletes old invoice items
4. Creates new invoice items
5. Items flushed
6. **Stock Service**: Records new OUT transactions
7. Changes committed

**Deleting Sales Invoice**:
1. Validates invoice is DRAFT or CANCELLED
2. **Stock Service**: Reverses OUT transactions (returns stock)
3. Soft-deletes invoice (is_deleted = True)

## Comparison with Purchase Invoice

| Aspect | Purchase Invoice | Sales Invoice |
|--------|------------------|---------------|
| Vendor/Customer Account | AR-{supplier_id} (LIABILITY) | AR-{customer_id} (ASSET) |
| Normal Balance | CREDIT | DEBIT |
| Invoice Voucher Dr | Purchase Expense + Taxes | Customer Receivable |
| Invoice Voucher Cr | Vendor Payable | Sales Revenue + Taxes |
| Payment Voucher Type | PAYMENT | RECEIPT |
| Payment Voucher Dr | Vendor Payable | Bank/Cash |
| Payment Voucher Cr | Bank/Cash | Customer Receivable |
| Stock Transaction | IN (increases inventory) | OUT (decreases inventory) |
| Reversal Transaction | OUT (reduces inventory) | IN (returns inventory) |

## Testing Recommendations

1. **Account Creation**:
   - Test with new customer (account created)
   - Test with existing customer (account reused)
   - Test without Accounts Receivable group configured

2. **Invoice with Taxes**:
   - Test with CGST+SGST (intra-state)
   - Test with IGST (inter-state)
   - Test with CESS
   - Verify voucher lines match invoice totals

3. **Payment Processing**:
   - Test single payment mode
   - Test multiple payment modes (partial cash, partial bank)
   - Test with bank account assignment
   - Verify receipt voucher balances

4. **Stock Tracking**:
   - Create invoice → verify stock OUT
   - Update invoice → verify reversal + new OUT
   - Delete invoice → verify stock returned
   - Check StockBalance quantities

5. **Error Scenarios**:
   - Missing account configurations
   - Duplicate customer account codes
   - Invalid voucher types
   - Insufficient stock

## Configuration Requirements

**Account Master Configurations** (in account_configuration_keys):
- `SALES_ACCOUNT` - Revenue account
- `CGST_OUTPUT_ACCOUNT` - CGST payable
- `SGST_OUTPUT_ACCOUNT` - SGST payable  
- `IGST_OUTPUT_ACCOUNT` - IGST payable
- `UGST_OUTPUT_ACCOUNT` - UGST payable (optional)
- `CESS_OUTPUT_ACCOUNT` - CESS payable (optional)
- `ACCOUNTS_RECEIVABLE` - AR group reference (optional, has fallback)
- `CASH` - Default cash account
- `BANK` - Default bank account

**Voucher Types Required**:
- `SALES` - For invoice vouchers
- `RECEIPT` - For payment vouchers

## Files Modified

1. `modules/inventory_module/services/sales_invoice_service.py`:
   - Added `_get_or_create_customer_account()` method
   - Updated `_create_sales_voucher()` to use customer account + CESS
   - Updated `_create_payment()` to change type to RECEIPT
   - Added `_create_payment_voucher()` method
   - Added stock transaction recording in `create()` method
   - Added stock reversal in `update()` method
   - Added stock reversal in `delete()` method

2. `modules/inventory_module/services/stock_service.py`:
   - Added `record_sales_invoice_transaction_in_session()` method
   - Added `reverse_sales_invoice_transaction_in_session()` method

## Implementation Date
January 2025
