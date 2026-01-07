# Payment Invoice Type Enhancement - Summary

## Changes Made

### 1. Created Payment Schemas in account_schema folder
**File**: `api/schemas/account_schema/payment_schemas.py`

- Created `InvoiceType` ENUM with values:
  - PURCHASE
  - SALES
  - TEST
  - CLINIC
  - EXPENSE
  - BILL
  - ADVANCE
  - DEBIT_NOTE
  - CREDIT_NOTE

- Created `PaymentMode` ENUM
- Created `PartyType` ENUM (includes PATIENT)
- Moved all payment request schemas to this file:
  - `InvoicePaymentRequest` - with invoice_type as InvoiceType ENUM
  - `AdvancePaymentRequest`
  - `GatewayPaymentUpdateRequest`
  - `PaymentMetadataUpdate`
  - `PaymentReversalRequest`

### 2. Updated Payments Route
**File**: `api/v1/routers/account_routes/payments_route.py`

- Removed local schema definitions
- Updated imports to use schemas from `api.schemas.account_schema.payment_schemas`
- Updated `create_invoice_payment` endpoint to use `request.invoice_type.value` (ENUM value)

### 3. Updated Payment Service
**File**: `modules/account_module/services/payment_service.py`

#### Method: `create_invoice_payment_simple`
- Added TEST invoice type handling:
  - Queries `TestInvoice` from `modules.health_module.models.test_invoice_entity`
  - Sets `payment_type = 'RECEIPT'`
  - Sets `party_type = 'PATIENT'`
  - Uses `patient_id` field from test invoice

#### Method: `_create_invoice_payment_voucher_simple`
- Updated to handle TEST invoice type:
  - Treats TEST as RECEIPT (like SALES)
  - Uses AR account directly for Patient receivables
  - Creates proper voucher lines with "Patient payment" description

#### Method: `confirm_gateway_payment`
- Added logic to detect TEST invoice type:
  - Checks if `payment.party_type == 'PATIENT'`
  - Queries TestInvoice when party type is PATIENT
  - Properly updates test invoice payment status

## Business Logic

### When TEST invoice type is selected:
1. System validates invoice exists in `test_invoices` table
2. Party type is automatically set to PATIENT
3. Patient ID is extracted from test invoice
4. Payment is treated as RECEIPT (money coming in)
5. Voucher entries:
   - Debit: Cash/Bank account
   - Credit: AR (Accounts Receivable) account
6. Test invoice payment status is updated accordingly

## API Usage Example

```json
POST /payments/invoice
{
  "payment_number": "PAY-001",
  "invoice_id": 123,
  "invoice_type": "TEST",
  "amount": 1500.00,
  "payment_mode": "CASH",
  "remarks": "Payment for lab tests"
}
```

## Validation
- Invoice type must be one of the ENUM values
- When TEST is selected, system validates test invoice exists
- Payment amount cannot exceed invoice balance
- Patient must exist in the system
