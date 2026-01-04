# Payment System V2 - Enhanced Payment Management

## Overview
The enhanced payment system now supports comprehensive payment tracking including:
- Multi-invoice/order allocation
- Payment gateway integration
- Refund handling
- Branch-wise payment tracking
- Source document linking
- Expense payments
- UPI, NEFT, RTGS, IMPS support

## Database Changes

### 1. Payments Table - New Fields

```sql
-- Branch tracking
branch_id              INTEGER REFERENCES branches(id)

-- Document linking
source_document_type   VARCHAR(20)  -- ORDER, INVOICE, EXPENSE, ADVANCE, BILL, OTHER
source_document_id     INTEGER

-- Allocation tracking
allocated_amount_base  NUMERIC(15,4) DEFAULT 0
unallocated_amount_base NUMERIC(15,4) DEFAULT 0

-- Refund handling
is_refund              BOOLEAN DEFAULT FALSE
original_payment_id    INTEGER REFERENCES payments(id)

-- Payment gateway
payment_gateway        VARCHAR(50)
gateway_transaction_id VARCHAR(100)
gateway_status         VARCHAR(20)
gateway_fee_base       NUMERIC(15,4) DEFAULT 0
gateway_response       JSONB
```

### 2. Payment Details Table - New Fields

```sql
branch_id              INTEGER REFERENCES branches(id)

-- Additional payment modes
payment_mode           VARCHAR(20)  -- Added: NEFT, RTGS, IMPS
```

### 3. New Table: Payment Allocations

```sql
CREATE TABLE payment_allocations (
    id                     SERIAL PRIMARY KEY,
    tenant_id              INTEGER NOT NULL,
    branch_id              INTEGER,
    payment_id             INTEGER NOT NULL,
    
    -- Document reference
    document_type          VARCHAR(20) NOT NULL,  -- ORDER, INVOICE, EXPENSE, BILL, etc.
    document_id            INTEGER NOT NULL,
    document_number        VARCHAR(50),
    
    -- Amounts
    allocated_amount_base  NUMERIC(15,4) NOT NULL,
    allocated_amount_foreign NUMERIC(15,4),
    discount_amount_base   NUMERIC(15,4) DEFAULT 0,
    adjustment_amount_base NUMERIC(15,4) DEFAULT 0,
    
    -- Metadata
    allocation_date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks                TEXT,
    
    -- Audit fields
    created_at, created_by, updated_at, updated_by, is_deleted
);
```

## API Changes

### New Endpoints

#### 1. Get Payment Allocations
```http
GET /api/v1/payments/{payment_id}/allocations
```
Returns all invoice/order allocations for a specific payment.

#### 2. Get Document Payments
```http
GET /api/v1/documents/{document_type}/{document_id}/payments
```
Returns all payments allocated to a specific invoice/order/expense.

**Example:**
```http
GET /api/v1/documents/INVOICE/123/payments
```

### Enhanced Endpoints

#### 1. Create Payment (Enhanced)
```http
POST /api/v1/payments
```

**Request Body:**
```json
{
  "payment_number": "PAY-2025-001",
  "payment_date": "2025-01-15T10:00:00",
  "payment_type": "RECEIPT",
  "party_type": "CUSTOMER",
  "party_id": 1,
  "branch_id": 1,
  
  "source_document_type": "INVOICE",
  "source_document_id": 123,
  
  "base_currency_id": 1,
  "total_amount_base": 10000.00,
  "allocated_amount_base": 10000.00,
  "unallocated_amount_base": 0.00,
  
  "payment_gateway": "Razorpay",
  "gateway_transaction_id": "pay_123456789",
  "gateway_status": "SUCCESS",
  "gateway_fee_base": 50.00,
  
  "status": "POSTED",
  "reference_number": "UTR123456",
  "remarks": "Payment for Invoice INV-001",
  
  "details": [
    {
      "line_no": 1,
      "payment_mode": "UPI",
      "transaction_reference": "123456789@paytm",
      "amount_base": 10000.00,
      "account_id": 1,
      "description": "UPI payment"
    }
  ],
  
  "allocations": [
    {
      "document_type": "INVOICE",
      "document_id": 101,
      "document_number": "INV-001",
      "allocated_amount_base": 4000.00,
      "discount_amount_base": 0.00,
      "remarks": "Partial payment"
    },
    {
      "document_type": "INVOICE",
      "document_id": 102,
      "document_number": "INV-002",
      "allocated_amount_base": 3000.00
    },
    {
      "document_type": "INVOICE",
      "document_id": 103,
      "document_number": "INV-003",
      "allocated_amount_base": 3000.00
    }
  ]
}
```

#### 2. Get Payments (Enhanced Filters)
```http
GET /api/v1/payments?branch_id=1&payment_type=RECEIPT&status=POSTED
```

**New Query Parameters:**
- `branch_id`: Filter by branch
- All existing filters remain

## Use Cases

### 1. Order Payment
```json
{
  "payment_type": "RECEIPT",
  "party_type": "CUSTOMER",
  "source_document_type": "ORDER",
  "source_document_id": 456,
  "allocations": [
    {
      "document_type": "ORDER",
      "document_id": 456,
      "allocated_amount_base": 5000.00
    }
  ]
}
```

### 2. Invoice Payment (Multiple Invoices)
```json
{
  "payment_type": "RECEIPT",
  "party_type": "CUSTOMER",
  "allocations": [
    {
      "document_type": "INVOICE",
      "document_id": 101,
      "allocated_amount_base": 2000.00
    },
    {
      "document_type": "INVOICE",
      "document_id": 102,
      "allocated_amount_base": 3000.00
    }
  ]
}
```

### 3. Expense Payment
```json
{
  "payment_type": "PAYMENT",
  "party_type": "SUPPLIER",
  "source_document_type": "EXPENSE",
  "source_document_id": 789,
  "allocations": [
    {
      "document_type": "EXPENSE",
      "document_id": 789,
      "allocated_amount_base": 1500.00
    }
  ]
}
```

### 4. UPI Payment
```json
{
  "details": [
    {
      "payment_mode": "UPI",
      "transaction_reference": "9876543210@paytm",
      "amount_base": 5000.00
    }
  ]
}
```

### 5. Bank Transfer (NEFT/RTGS/IMPS)
```json
{
  "details": [
    {
      "payment_mode": "NEFT",
      "bank_account_id": 1,
      "transaction_reference": "NEFT123456789",
      "amount_base": 10000.00
    }
  ]
}
```

### 6. Payment Gateway Integration
```json
{
  "payment_gateway": "Razorpay",
  "gateway_transaction_id": "pay_123456789",
  "gateway_status": "SUCCESS",
  "gateway_fee_base": 50.00,
  "gateway_response": "{\"order_id\":\"order_123\",\"status\":\"captured\"}"
}
```

### 7. Refund Processing
```json
{
  "payment_type": "PAYMENT",
  "is_refund": true,
  "original_payment_id": 100,
  "total_amount_base": 1000.00,
  "remarks": "Refund for cancelled order"
}
```

## Validation Rules

### 1. Allocation Validation
- Total allocated amount cannot exceed payment amount
- `allocated_amount_base + unallocated_amount_base <= total_amount_base`

### 2. Payment Mode Validation
Valid modes: CASH, BANK, CARD, UPI, CHEQUE, ONLINE, WALLET, NEFT, RTGS, IMPS

### 3. Document Type Validation
Valid types: ORDER, INVOICE, EXPENSE, BILL, ADVANCE, DEBIT_NOTE, CREDIT_NOTE

### 4. Status Validation
Valid statuses: DRAFT, POSTED, CANCELLED, RECONCILED

### 5. Deletion Rules
- Only DRAFT or CANCELLED payments can be deleted
- Deletion is soft delete (is_deleted = true)

## Accounting Impact

### Payment Receipt (Customer)
```
Dr. Bank/Cash Account          $10,000
    Cr. Accounts Receivable            $10,000
```

### Payment Made (Supplier)
```
Dr. Accounts Payable           $10,000
    Cr. Bank/Cash Account              $10,000
```

### Important Notes:
1. **No additional GL entries for allocations** - Allocations are sub-ledger tracking only
2. **Revenue accounts are NOT touched** - They were credited when invoice was created
3. **One payment = One voucher** - Regardless of how many invoices it's applied to

## Migration Guide

### For Existing Code

1. **Update Entity Imports:**
```python
from modules.account_module.models.payment_entity import Payment, PaymentDetail, PaymentAllocation
```

2. **Use New Service:**
```python
from modules.account_module.services.payment_service_v2 import PaymentServiceV2
payment_service = PaymentServiceV2()
```

3. **Update Routes:**
```python
from api.v1.routers.account_routes.payments_route_v2 import router
```

### Database Migration

Run the updated schema:
```bash
psql -U postgres -d your_database -f database/schemas/payments.sql
```

## Branch-Wise Reporting

### Get Branch Payments
```http
GET /api/v1/payments?branch_id=1&date_from=2025-01-01&date_to=2025-01-31
```

### Branch-Wise Collection Report
```sql
SELECT 
    b.name as branch_name,
    COUNT(p.id) as payment_count,
    SUM(p.total_amount_base) as total_collection
FROM payments p
JOIN branches b ON p.branch_id = b.id
WHERE p.payment_type = 'RECEIPT'
  AND p.status = 'POSTED'
  AND p.payment_date BETWEEN '2025-01-01' AND '2025-01-31'
GROUP BY b.id, b.name;
```

## Best Practices

1. **Always provide allocations** when payment is for specific invoices/orders
2. **Use source_document fields** to link payment to originating document
3. **Set branch_id** for branch-wise tracking and reporting
4. **Store gateway_response** as JSON string for audit trail
5. **Use unallocated_amount_base** to track advance payments
6. **Mark refunds properly** with is_refund=true and original_payment_id

## Error Handling

### Common Errors

1. **Duplicate Payment Number**
```json
{
  "detail": "Payment number 'PAY-2025-001' already exists"
}
```

2. **Allocation Exceeds Total**
```json
{
  "detail": "Total allocated amount cannot exceed payment amount"
}
```

3. **Cannot Delete Posted Payment**
```json
{
  "detail": "Cannot delete payment with status 'POSTED'"
}
```

4. **Already Reconciled**
```json
{
  "detail": "Payment is already reconciled"
}
```

## Testing

### Test Scenarios

1. ✅ Create payment with single invoice allocation
2. ✅ Create payment with multiple invoice allocations
3. ✅ Create payment with partial allocation (unallocated amount)
4. ✅ Create UPI payment
5. ✅ Create NEFT/RTGS payment
6. ✅ Create payment gateway payment
7. ✅ Create refund payment
8. ✅ Update payment allocations
9. ✅ Reconcile payment
10. ✅ Branch-wise filtering
11. ✅ Get document payments
12. ✅ Validate allocation constraints

## Support

For issues or questions:
1. Check validation rules above
2. Review use case examples
3. Verify database schema is updated
4. Check entity relationships are properly configured
