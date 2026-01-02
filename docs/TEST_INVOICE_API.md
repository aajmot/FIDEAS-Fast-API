# Test Invoice API Implementation

## Overview
Complete REST API implementation for test invoices with proper transaction handling and automatic voucher creation.

## Architecture

### 1. Models Layer
**File**: `modules/health_module/models/test_invoice_entity.py`

- `TestInvoice`: Main invoice entity with all financial fields
- `TestInvoiceItem`: Line items for tests/panels with tax calculations
- Relationships: Links to vouchers, test orders, patients

### 2. Schema Layer
**File**: `api/schemas/health_schema/test_invoice_schema.py`

- `TestInvoiceItemSchema`: Validation for invoice line items
- `TestInvoiceCreateSchema`: Create invoice with items (minimum 1 item required)
- `TestInvoiceUpdateSchema`: Update invoice metadata (status, notes, tags)

### 3. Service Layer
**File**: `modules/health_module/services/test_invoice_service.py`

Key Features:
- **Transaction Management**: All operations wrapped in database transactions
- **Voucher Creation**: Automatic voucher generation when status = 'POSTED'
- **Voucher Entries**:
  - Debit: Accounts Receivable (Patient)
  - Credit: Revenue Account
- **Filtering**: Support for search, status, payment_status filters
- **Pagination**: Built-in pagination support

### 4. Router Layer
**File**: `api/v1/routers/health_routes/testinvoices_route.py`

## API Endpoints

### 1. Create Test Invoice
```
POST /api/v1/health/testinvoices
```

**Request Body**:
```json
{
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15T10:30:00",
  "due_date": "2024-02-15",
  "test_order_id": 123,
  "patient_id": 45,
  "patient_name": "John Doe",
  "patient_phone": "9876543210",
  "subtotal_amount": 1000.00,
  "items_total_discount_amount": 50.00,
  "taxable_amount": 950.00,
  "cgst_amount": 85.50,
  "sgst_amount": 85.50,
  "overall_disc_percentage": 0,
  "overall_disc_amount": 0,
  "roundoff": 0.50,
  "final_amount": 1121.50,
  "status": "POSTED",
  "notes": "Regular checkup invoice",
  "tags": ["routine", "paid"],
  "items": [
    {
      "line_no": 1,
      "test_id": 10,
      "test_name": "Blood Test",
      "rate": 500.00,
      "disc_percentage": 5,
      "disc_amount": 25.00,
      "taxable_amount": 475.00,
      "cgst_rate": 9,
      "cgst_amount": 42.75,
      "sgst_rate": 9,
      "sgst_amount": 42.75,
      "total_amount": 560.50
    },
    {
      "line_no": 2,
      "panel_id": 5,
      "panel_name": "Diabetes Panel",
      "rate": 500.00,
      "disc_percentage": 5,
      "disc_amount": 25.00,
      "taxable_amount": 475.00,
      "cgst_rate": 9,
      "cgst_amount": 42.75,
      "sgst_rate": 9,
      "sgst_amount": 42.75,
      "total_amount": 560.50
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Test invoice created successfully",
  "data": {
    "id": 1
  }
}
```

**Transaction Behavior**:
- Creates invoice record
- Creates all invoice items
- If status = 'POSTED', creates voucher with entries:
  - Voucher number auto-generated (format: TINV{YYYYMMDD}{SEQ})
  - Debit entry: Accounts Receivable
  - Credit entry: Revenue Account
- All operations in single transaction (rollback on any error)

### 2. Get Invoice by ID
```
GET /api/v1/health/testinvoices/{invoice_id}
```

**Response**:
```json
{
  "success": true,
  "message": "Test invoice retrieved successfully",
  "data": {
    "id": 1,
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15T10:30:00",
    "patient_name": "John Doe",
    "final_amount": 1121.50,
    "paid_amount": 0,
    "payment_status": "UNPAID",
    "status": "POSTED",
    "voucher_id": 100,
    "items": [...]
  }
}
```

### 3. Get All Invoices (with Filters & Pagination)
```
GET /api/v1/health/testinvoices?page=1&per_page=10&search=John&status=POSTED&payment_status=UNPAID
```

**Query Parameters**:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10, max: 100)
- `search`: Search in invoice_number, patient_name
- `status`: Filter by status (DRAFT, POSTED, CANCELLED)
- `payment_status`: Filter by payment status (UNPAID, PARTIAL, PAID, OVERPAID)

**Response**:
```json
{
  "success": true,
  "message": "Test invoices retrieved successfully",
  "data": [...],
  "total": 50,
  "page": 1,
  "per_page": 10,
  "total_pages": 5
}
```

### 4. Update Invoice
```
PUT /api/v1/health/testinvoices/{invoice_id}
```

**Request Body** (all fields optional):
```json
{
  "status": "CANCELLED",
  "notes": "Cancelled due to duplicate entry",
  "tags": ["cancelled"]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Test invoice updated successfully"
}
```

## Database Schema

### test_invoices Table
- Primary fields: invoice_number, invoice_date, due_date
- Financial: subtotal, discounts, taxes, roundoff, final_amount
- Payment tracking: paid_amount, balance_amount (computed), payment_status
- Status: status (DRAFT/POSTED/CANCELLED)
- Accounting: voucher_id (FK to vouchers)
- Audit: created_at, created_by, updated_at, updated_by

### test_invoice_items Table
- Line items with test_id or panel_id
- Rate, discounts, taxes per line
- Total amount calculation

## Transaction Flow

1. **Invoice Creation**:
   ```
   BEGIN TRANSACTION
     → Insert test_invoice
     → Insert test_invoice_items (all items)
     → If status = 'POSTED':
         → Generate voucher_number
         → Insert voucher
         → Insert voucher_lines (debit + credit)
         → Update invoice.voucher_id
   COMMIT
   ```

2. **Error Handling**:
   - Any error triggers automatic rollback
   - No partial data saved
   - Proper error logging

## Key Features

✅ **Transaction Safety**: All operations atomic
✅ **Voucher Integration**: Auto-creates accounting entries
✅ **Validation**: Pydantic schemas validate all inputs
✅ **Filtering**: Search, status, payment_status filters
✅ **Pagination**: Efficient data retrieval
✅ **Audit Trail**: Created/updated by tracking
✅ **Multi-tenant**: Tenant isolation enforced
✅ **Authentication**: JWT token required

## Configuration Notes

### Account Mapping (TODO)
Currently hardcoded account IDs in service:
- `account_id=1`: Accounts Receivable
- `account_id=2`: Revenue Account

**Production Setup**: Map to actual account masters:
```python
# Get from account_masters where system_code = 'ACCOUNTS_RECEIVABLE'
# Get from account_masters where system_code = 'TEST_REVENUE'
```

### Voucher Type
Service looks for voucher_type with code='SALES'
Fallback to first available voucher type if not found

## Testing

### Create Invoice (DRAFT)
```bash
curl -X POST http://localhost:8000/api/v1/health/testinvoices \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Create Invoice (POSTED - with voucher)
Set `"status": "POSTED"` in request body

### Get with Filters
```bash
curl "http://localhost:8000/api/v1/health/testinvoices?status=POSTED&payment_status=UNPAID&page=1&per_page=20" \
  -H "Authorization: Bearer {token}"
```

## Future Enhancements

1. **Payment Allocation**: Link payments to invoices
2. **Credit Notes**: Support for invoice reversals
3. **Email Notifications**: Send invoice to patient
4. **PDF Generation**: Generate printable invoices
5. **Batch Operations**: Bulk invoice creation
6. **Advanced Reporting**: Revenue analytics

## Files Created

1. `modules/health_module/models/test_invoice_entity.py` - Models
2. `api/schemas/health_schema/test_invoice_schema.py` - Schemas
3. `modules/health_module/services/test_invoice_service.py` - Service
4. `api/v1/routers/health_routes/testinvoices_route.py` - Router
5. Updated `api/main.py` - Route registration
6. Updated `api/v1/routers/health_routes/__init__.py` - Export

## Summary

Complete test invoice API with:
- ✅ Create with items
- ✅ Get by ID
- ✅ Get all with filters & pagination
- ✅ Update
- ✅ Transaction-safe operations
- ✅ Automatic voucher creation
- ✅ Proper separation of concerns (Model/Schema/Service/Router)
