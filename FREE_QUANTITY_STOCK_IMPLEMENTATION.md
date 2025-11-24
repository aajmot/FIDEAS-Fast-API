# Free Quantity Stock Implementation

## Overview
Implemented free quantity tracking for both sales and purchase invoices. Free quantities (complimentary/bonus items) now impact inventory stock levels correctly.

## Changes Made

### 1. Database Schema Updates

#### Migration File Created
- **File**: `database/migrations/add_free_quantity_to_invoices.sql`
- Added `free_quantity` column to both `purchase_invoice_items` and `sales_invoice_items` tables
- Type: `NUMERIC(15,4) DEFAULT 0`

#### Schema Files Updated
- **purchase_invoices.sql**: Added `free_quantity` field after `quantity` field
- **sales_invoices.sql**: Added `free_quantity` field after `quantity` field

### 2. Entity Models Updated

#### Purchase Invoice Entity
- **File**: `modules/inventory_module/models/purchase_invoice_entity.py`
- Added `free_quantity = Column(Numeric(15, 4), default=0)` to `PurchaseInvoiceItem` class

#### Sales Invoice Entity
- **File**: `modules/inventory_module/models/sales_invoice_entity.py`
- Added `free_quantity = Column(Numeric(15, 4), default=0)` to `SalesInvoiceItem` class

### 3. Stock Service Updates

#### Updated Methods in `modules/inventory_module/services/stock_service.py`:

1. **`record_purchase_invoice_transaction_in_session()`**
   - Now calculates `total_qty = quantity + free_quantity`
   - Records stock IN transaction with total quantity
   - Updates stock balance with total quantity

2. **`reverse_purchase_invoice_transaction_in_session()`**
   - Reverses using total quantity (quantity + free_quantity)

3. **`record_sales_invoice_transaction_in_session()`**
   - Now calculates `total_qty = quantity + free_quantity`
   - Records stock OUT transaction with total quantity
   - Updates stock balance with total quantity

4. **`reverse_sales_invoice_transaction_in_session()`**
   - Reverses using total quantity (quantity + free_quantity)

### 4. Purchase Invoice Service Updates

#### File: `modules/inventory_module/services/purchase_invoice_service.py`

**Create Method**:
- Added `free_quantity=item_data.get('free_quantity', 0)` when creating `PurchaseInvoiceItem`

**Update Method**:
- Added `free_quantity=item_data.get('free_quantity', 0)` when creating new items

**_item_to_dict Method**:
- Added `'free_quantity': item.free_quantity` to item dictionary

### 5. Sales Invoice Service Updates

#### File: `modules/inventory_module/services/sales_invoice_service.py`

**Create Method**:
- Added `free_quantity=item_data.get('free_quantity', 0)` when creating `SalesInvoiceItem`

**Update Method**:
- Added default `free_quantity` value check before creating items
- Ensures `free_quantity` defaults to 0 if not provided

**_to_dict Method**:
- Added `'free_quantity': float(item.free_quantity) if item.free_quantity else 0.0` to item dictionary

### 6. Additional Bug Fixes Applied

While implementing free quantity, also fixed critical issues:

1. **GST Check Constraint Violation**:
   - Fixed rounding errors in GST amount calculations
   - Now recalculates `tax_amount_base` as sum of all GST components after rounding

2. **Total Amount Calculation**:
   - Fixed formula: `total_amount_base = subtotal_base + tax_amount_base`
   - Was incorrectly using subtotal without adding tax

3. **Negative Balance Prevention**:
   - Added rounding to 2 decimal places for balance amounts
   - Prevents tiny negative balances due to rounding errors
   - Sets balance to 0 if negative amount is < 0.01

4. **Decimal Type Handling**:
   - All amounts properly converted to `Decimal` type
   - Fixed Pydantic serialization warnings

## Impact on Stock Transactions

### Purchase Invoice
**Before**: Only `quantity` was added to stock
**After**: `quantity + free_quantity` is added to stock

Example:
- Quantity: 100 units @ $10 each
- Free Quantity: 10 units (free of cost)
- **Stock Impact**: 110 units added (100 paid + 10 free)
- **Cost Basis**: Distributed across all 110 units

### Sales Invoice
**Before**: Only `quantity` was deducted from stock
**After**: `quantity + free_quantity` is deducted from stock

Example:
- Quantity: 50 units @ $15 each
- Free Quantity: 5 units (complimentary)
- **Stock Impact**: 55 units deducted (50 sold + 5 free)
- **Revenue**: Only recorded for 50 units

## Usage

### API Request Format

#### Purchase Invoice with Free Quantity
```json
{
  "items": [
    {
      "product_id": 123,
      "quantity": 100,
      "free_quantity": 10,
      "unit_price_base": 10.00
    }
  ]
}
```

#### Sales Invoice with Free Quantity
```json
{
  "items": [
    {
      "product_id": 123,
      "quantity": 50,
      "free_quantity": 5,
      "unit_price_base": 15.00
    }
  ]
}
```

## Database Migration

To apply the changes to an existing database:

```sql
-- Run the migration
\i database/migrations/add_free_quantity_to_invoices.sql
```

## Backward Compatibility

- Existing records without `free_quantity` will default to 0
- API accepts requests without `free_quantity` field (defaults to 0)
- No breaking changes to existing functionality

## Testing Recommendations

1. **Create Purchase Invoice** with free quantity
2. **Verify Stock Balance** includes total quantity
3. **Create Sales Invoice** with free quantity
4. **Verify Stock Deduction** includes total quantity
5. **Test Reversal Operations** for both invoice types
6. **Verify Accounting Entries** (free quantity has no cost impact)

## Notes

- Free quantity items are tracked in inventory but have no cost/revenue impact
- Useful for tracking promotional items, samples, or bonus products
- Stock valuation uses weighted average cost across paid + free quantities
- Reporting should distinguish between paid and free quantities where relevant
