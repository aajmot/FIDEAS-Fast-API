# Payment System V2 - Quick Reference Guide

## 🚀 Quick Start

### 1. Import Required Modules
```python
from modules.account_module.services.payment_service_v2 import PaymentServiceV2
from modules.account_module.models.payment_schemas import PaymentRequest, PaymentAllocationRequest, PaymentDetailRequest

payment_service = PaymentServiceV2()
```

### 2. Create Simple Payment
```python
payment_data = {
    "payment_number": "PAY-2025-001",
    "payment_date": datetime.now(),
    "payment_type": "RECEIPT",
    "party_type": "CUSTOMER",
    "party_id": 1,
    "base_currency_id": 1,
    "total_amount_base": 5000.00,
    "status": "POSTED",
    "details": [
        {
            "line_no": 1,
            "payment_mode": "UPI",
            "amount_base": 5000.00,
            "transaction_reference": "123456@paytm"
        }
    ]
}

result = payment_service.create_payment(payment_data)
```

### 3. Create Payment with Allocations
```python
payment_data = {
    "payment_number": "PAY-2025-002",
    "payment_date": datetime.now(),
    "payment_type": "RECEIPT",
    "party_type": "CUSTOMER",
    "party_id": 1,
    "branch_id": 1,
    "base_currency_id": 1,
    "total_amount_base": 10000.00,
    "allocated_amount_base": 10000.00,
    "unallocated_amount_base": 0.00,
    "status": "POSTED",
    "details": [
        {
            "line_no": 1,
            "payment_mode": "BANK",
            "amount_base": 10000.00,
            "bank_account_id": 1,
            "transaction_reference": "NEFT123456"
        }
    ],
    "allocations": [
        {
            "document_type": "INVOICE",
            "document_id": 101,
            "document_number": "INV-001",
            "allocated_amount_base": 4000.00
        },
        {
            "document_type": "INVOICE",
            "document_id": 102,
            "document_number": "INV-002",
            "allocated_amount_base": 6000.00
        }
    ]
}

result = payment_service.create_payment(payment_data)
```

## 📋 Common Scenarios

### Scenario 1: Customer Payment via UPI
```python
{
    "payment_type": "RECEIPT",
    "party_type": "CUSTOMER",
    "party_id": 123,
    "branch_id": 1,
    "total_amount_base": 5000.00,
    "details": [{
        "line_no": 1,
        "payment_mode": "UPI",
        "transaction_reference": "9876543210@paytm",
        "amount_base": 5000.00
    }],
    "allocations": [{
        "document_type": "INVOICE",
        "document_id": 456,
        "allocated_amount_base": 5000.00
    }]
}
```

### Scenario 2: Supplier Payment via NEFT
```python
{
    "payment_type": "PAYMENT",
    "party_type": "SUPPLIER",
    "party_id": 789,
    "branch_id": 1,
    "total_amount_base": 15000.00,
    "details": [{
        "line_no": 1,
        "payment_mode": "NEFT",
        "bank_account_id": 1,
        "transaction_reference": "NEFT987654321",
        "amount_base": 15000.00
    }],
    "allocations": [{
        "document_type": "BILL",
        "document_id": 321,
        "allocated_amount_base": 15000.00
    }]
}
```

### Scenario 3: Expense Payment
```python
{
    "payment_type": "PAYMENT",
    "party_type": "SUPPLIER",
    "source_document_type": "EXPENSE",
    "source_document_id": 555,
    "total_amount_base": 2000.00,
    "details": [{
        "line_no": 1,
        "payment_mode": "CASH",
        "amount_base": 2000.00
    }],
    "allocations": [{
        "document_type": "EXPENSE",
        "document_id": 555,
        "allocated_amount_base": 2000.00
    }]
}
```

### Scenario 4: Payment Gateway (Razorpay)
```python
{
    "payment_type": "RECEIPT",
    "party_type": "CUSTOMER",
    "payment_gateway": "Razorpay",
    "gateway_transaction_id": "pay_123456789",
    "gateway_status": "SUCCESS",
    "gateway_fee_base": 50.00,
    "gateway_response": '{"order_id":"order_123","status":"captured"}',
    "total_amount_base": 5000.00,
    "details": [{
        "line_no": 1,
        "payment_mode": "ONLINE",
        "amount_base": 5000.00
    }]
}
```

### Scenario 5: Refund
```python
{
    "payment_type": "PAYMENT",
    "party_type": "CUSTOMER",
    "is_refund": True,
    "original_payment_id": 100,
    "total_amount_base": 1000.00,
    "remarks": "Refund for cancelled order",
    "details": [{
        "line_no": 1,
        "payment_mode": "BANK",
        "amount_base": 1000.00
    }]
}
```

### Scenario 6: Partial Payment (Advance)
```python
{
    "payment_type": "RECEIPT",
    "party_type": "CUSTOMER",
    "total_amount_base": 10000.00,
    "allocated_amount_base": 7000.00,
    "unallocated_amount_base": 3000.00,  # Advance
    "advance_amount_base": 3000.00,
    "details": [{
        "line_no": 1,
        "payment_mode": "BANK",
        "amount_base": 10000.00
    }],
    "allocations": [{
        "document_type": "INVOICE",
        "document_id": 101,
        "allocated_amount_base": 7000.00
    }]
}
```

## 🔍 Query Examples

### Get All Payments
```python
payments = payment_service.get_all_payments(
    page=1,
    page_size=50,
    payment_type="RECEIPT",
    status="POSTED",
    branch_id=1
)
```

### Get Payment by ID
```python
payment = payment_service.get_payment_by_id(123)
```

### Get Payment Allocations
```python
allocations = payment_service.get_payment_allocations(123)
```

### Get Payments for an Invoice
```python
payments = payment_service.get_document_payments("INVOICE", 456)
```

### Update Payment
```python
updated_data = {
    "status": "RECONCILED",
    "remarks": "Updated remarks"
}
payment = payment_service.update_payment(123, updated_data)
```

### Reconcile Payment
```python
payment = payment_service.reconcile_payment(123, datetime.now())
```

### Delete Payment
```python
success = payment_service.delete_payment(123)  # Only DRAFT or CANCELLED
```

## 🎯 Field Reference

### Payment Types
- `RECEIPT` - Money received
- `PAYMENT` - Money paid
- `CONTRA` - Bank to bank transfer

### Party Types
- `CUSTOMER` - Customer payment
- `SUPPLIER` - Supplier payment
- `EMPLOYEE` - Employee payment
- `BANK` - Bank transaction
- `PATIENT` - Patient payment (healthcare)
- `OTHER` - Other party

### Payment Modes
- `CASH` - Cash payment
- `BANK` - Bank transfer
- `CARD` - Card payment
- `UPI` - UPI payment
- `CHEQUE` - Cheque payment
- `ONLINE` - Online payment
- `WALLET` - Wallet payment
- `NEFT` - NEFT transfer
- `RTGS` - RTGS transfer
- `IMPS` - IMPS transfer

### Document Types
- `ORDER` - Sales/Purchase order
- `INVOICE` - Sales/Purchase invoice
- `EXPENSE` - Expense
- `BILL` - Bill
- `ADVANCE` - Advance payment
- `DEBIT_NOTE` - Debit note
- `CREDIT_NOTE` - Credit note

### Payment Status
- `DRAFT` - Not yet posted
- `POSTED` - Posted to accounts
- `CANCELLED` - Cancelled
- `RECONCILED` - Reconciled with bank

## ⚠️ Important Rules

### 1. Allocation Rules
```python
# Total allocated cannot exceed payment amount
allocated_amount_base + unallocated_amount_base <= total_amount_base
```

### 2. Deletion Rules
```python
# Only DRAFT or CANCELLED can be deleted
if payment.status not in ['DRAFT', 'CANCELLED']:
    raise ValueError("Cannot delete")
```

### 3. Reconciliation Rules
```python
# Cannot reconcile already reconciled payment
if payment.is_reconciled:
    raise ValueError("Already reconciled")
```

## 🔧 API Endpoints

### Base URL
```
/api/v1/payments
```

### Endpoints
```
GET    /payments                           # List all payments
GET    /payments/{id}                      # Get single payment
POST   /payments                           # Create payment
PUT    /payments/{id}                      # Update payment
DELETE /payments/{id}                      # Delete payment
POST   /payments/{id}/reconcile            # Reconcile payment
GET    /payments/{id}/allocations          # Get allocations
GET    /documents/{type}/{id}/payments     # Get document payments
```

## 📊 SQL Queries for Reports

### Branch-Wise Collection
```sql
SELECT 
    b.name,
    COUNT(p.id) as count,
    SUM(p.total_amount_base) as total
FROM payments p
JOIN branches b ON p.branch_id = b.id
WHERE p.payment_type = 'RECEIPT'
  AND p.status = 'POSTED'
GROUP BY b.id, b.name;
```

### Payment Mode Distribution
```sql
SELECT 
    pd.payment_mode,
    COUNT(*) as count,
    SUM(pd.amount_base) as total
FROM payment_details pd
JOIN payments p ON pd.payment_id = p.id
WHERE p.status = 'POSTED'
GROUP BY pd.payment_mode;
```

### Unallocated Payments
```sql
SELECT 
    payment_number,
    total_amount_base,
    unallocated_amount_base
FROM payments
WHERE unallocated_amount_base > 0
  AND status = 'POSTED';
```

### Invoice Payment Status
```sql
SELECT 
    pa.document_number,
    SUM(pa.allocated_amount_base) as paid,
    pa.document_id
FROM payment_allocations pa
WHERE pa.document_type = 'INVOICE'
GROUP BY pa.document_id, pa.document_number;
```

## 🐛 Common Errors & Solutions

### Error: "Payment number already exists"
**Solution:** Use unique payment number or query existing first

### Error: "Total allocated amount cannot exceed payment amount"
**Solution:** Check allocation amounts sum

### Error: "Cannot delete payment with status 'POSTED'"
**Solution:** Only delete DRAFT or CANCELLED payments

### Error: "Payment is already reconciled"
**Solution:** Check reconciliation status before reconciling

## 💡 Best Practices

1. ✅ Always provide allocations for invoice/order payments
2. ✅ Set branch_id for multi-branch operations
3. ✅ Use source_document fields for audit trail
4. ✅ Store gateway_response for payment gateways
5. ✅ Mark refunds with is_refund=true
6. ✅ Use unallocated_amount_base for advances
7. ✅ Validate allocation amounts before submission
8. ✅ Use proper payment modes (UPI, NEFT, etc.)
9. ✅ Add meaningful remarks for audit
10. ✅ Reconcile payments regularly

## 📞 Need Help?

- Check full documentation: `docs/PAYMENT_SYSTEM_V2.md`
- Review changes summary: `docs/PAYMENT_CHANGES_SUMMARY.md`
- Check entity models: `modules/account_module/models/payment_entity.py`
- Check schemas: `modules/account_module/models/payment_schemas.py`
- Check service: `modules/account_module/services/payment_service_v2.py`
