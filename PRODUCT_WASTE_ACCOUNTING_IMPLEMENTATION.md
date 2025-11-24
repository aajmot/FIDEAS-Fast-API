# Product Waste Stock & Accounting Implementation

## Overview
Enhanced product waste functionality to include:
1. Automatic stock transaction recording (OUT) for waste
2. Proper double-entry accounting vouchers for waste expense
3. Integration with inventory management system
4. Automatic account creation with fallback logic

## Implementation Details

### 1. Stock Management
**Integration**: Uses existing `StockService.record_waste_transaction_in_session()` method

**Stock Flow**:
- **Transaction Type**: `OUT` (reduces inventory)
- **Transaction Source**: `WASTE`
- **Reference**: Links to product waste record
- Records quantity and cost for each waste item
- Updates `StockBalance` to reduce available inventory

### 2. Accounting Voucher Creation
**File**: `modules/inventory_module/services/product_waste_service.py`
**Method**: `_create_waste_voucher()`

**Voucher Type**: `JOURNAL`

**Accounting Entries** (Double-Entry Bookkeeping):
```
Dr: Waste & Spoilage Expense (EXPENSE)    = Total Waste Cost
Cr: Inventory (ASSET)                     = Total Waste Cost
```

**Features**:
- Creates JOURNAL voucher with voucher number `JV-WASTE-{waste_number}`
- Records both base currency amounts
- Links voucher to waste record via `reference_type='PRODUCT_WASTE'`
- Updates waste record with `voucher_id` after creation
- Uses configured accounts with multiple fallback strategies

### 3. Account Configuration
**Required Accounts**:
- `WASTE_EXPENSE` - Expense account for waste and spoilage
- `INVENTORY` - Asset account for inventory value

**Fallback Logic**:

**For WASTE_EXPENSE**:
1. Uses tenant-configured `WASTE_EXPENSE` account setting
2. Falls back to any EXPENSE account with "waste" in name/system_code
3. Auto-creates "Waste & Spoilage Expense" account if not found

**For INVENTORY**:
1. Uses tenant-configured `INVENTORY` account setting
2. Falls back to any ASSET account with "inventory" or "stock" in name
3. Auto-creates "Inventory" account if not found

### 4. Auto-Created Accounts
**Method**: `_create_default_waste_account()`, `_create_default_inventory_account()`

**Waste Expense Account**:
- Name: "Waste & Spoilage Expense"
- Code: `WASTE-EXP-001`
- System Code: `WASTE_EXPENSE`
- Type: `EXPENSE`
- Normal Balance: `DEBIT`
- Links to Expenses group (auto-created if needed)

**Inventory Account**:
- Name: "Inventory"
- Code: `INV-001`
- System Code: `INVENTORY`
- Type: `ASSET`
- Normal Balance: `DEBIT`
- Links to Assets group (auto-created if needed)

### 5. Complete Flow

**Creating Product Waste**:
1. Waste header and items created
2. For each waste item:
   - Calculate total cost (quantity × unit_cost)
   - **Stock Service**: Records OUT transaction (reduces inventory)
3. Calculate header totals
4. **Accounting**: Creates JOURNAL voucher:
   - Dr: Waste Expense
   - Cr: Inventory
5. Link voucher to waste record
6. Commit transaction

**Accounting Impact**:
- **Expense Account** (Debit): Increases expense (reduces profit)
- **Inventory Account** (Credit): Decreases asset value
- **Stock Balance**: Reduces available quantity
- **Financial Statements**: 
  - Income Statement: Increases expenses
  - Balance Sheet: Reduces inventory asset value

### 6. Error Handling
- If voucher creation fails, error is logged but waste record is still created
- Prevents data loss while alerting about accounting issues
- Stock transactions still recorded even if accounting fails

## Accounting Logic Explanation

**Why this works**:
- **Waste Expense (Dr)**: Debit increases expense accounts
  - Represents the cost of products that were wasted/spoiled
  - Reduces net income on P&L
  
- **Inventory (Cr)**: Credit decreases asset accounts
  - Reduces the value of inventory on hand
  - Reflects products no longer available for sale

**Example**:
```
Product A: 10 units @ ₹100 each = ₹1,000 wasted

Journal Entry:
Dr: Waste & Spoilage Expense    ₹1,000
Cr: Inventory                   ₹1,000

Effect:
- Inventory reduced from ₹10,000 to ₹9,000
- Waste expense of ₹1,000 recorded
- Stock quantity reduced by 10 units
```

## Configuration Requirements

**Account Configuration Keys** (in account_configuration_keys):
- `WASTE_EXPENSE` - Waste & Spoilage Expense account
- `INVENTORY` - Inventory asset account

**Voucher Types Required**:
- `JOURNAL` - For waste transactions

**Optional but Recommended**:
- Pre-configure accounts in Account Master
- Set up account configurations in Account Configuration

## Files Modified

1. `modules/inventory_module/services/product_waste_service.py`:
   - Added `_create_waste_voucher()` method
   - Added `_get_configured_account()` method with fallback logic
   - Added `_create_default_waste_account()` method
   - Added `_create_default_inventory_account()` method
   - Updated `create()` to call voucher creation
   - Removed old `_record_accounting_transaction_in_session()` method

## Testing Recommendations

1. **Basic Waste Recording**:
   - Create waste record with single item
   - Verify stock OUT transaction created
   - Verify journal voucher created
   - Check inventory balance reduced

2. **Multiple Items**:
   - Create waste with multiple products
   - Verify totals calculated correctly
   - Check separate stock transactions per item
   - Verify single voucher with correct total

3. **Account Configuration**:
   - Test with configured accounts
   - Test without configuration (auto-creation)
   - Verify fallback logic works

4. **Financial Reports**:
   - Check expense shows in P&L
   - Verify inventory reduction in Balance Sheet
   - Confirm voucher appears in General Ledger

5. **Error Scenarios**:
   - Missing voucher type
   - Missing account configuration
   - Invalid product/warehouse

## Benefits

1. **Accurate Financial Reporting**: Waste expenses properly recorded
2. **Real-time Inventory Tracking**: Stock automatically adjusted
3. **Audit Trail**: Complete record of waste transactions
4. **Automated Accounting**: No manual journal entries needed
5. **Flexible Configuration**: Multiple fallback strategies
6. **Error Resilient**: Continues operation even if accounting fails

## Implementation Date
November 2025
