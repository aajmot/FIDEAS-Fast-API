# Changelog

## [Unreleased]

### Added
- Added `party_name` (VARCHAR 200, NOT NULL) and `party_phone` (VARCHAR 20, NOT NULL) fields to payments table
- Updated PaymentRequest schema to include party_name and party_phone as required fields
- Updated PaymentResponse schema to include party_name and party_phone fields
- Updated Payment entity model with party_name and party_phone columns
- Updated payment service methods (create_payment, update_payment, create_advance_payment, create_invoice_payment_simple) to handle party_name and party_phone
- Updated _payment_to_dict method to include party_name and party_phone in response
- Updated AdvancePaymentRequest schema to include party_name and party_phone as required fields
- Updated InvoicePaymentRequest schema to include party_name and party_phone as required fields
- Updated payment route endpoints (create_advance_customer_payment, create_invoice_payment) to pass party_name and party_phone to service methods

### Changed
- Payment CRUD APIs now require party_name and party_phone in request payload
- All payment responses now include party_name and party_phone fields
- Advance payment endpoint (/payments/advance/customer) now requires party_name and party_phone
- Invoice payment endpoint (/payments/invoice) now requires party_name and party_phone


## [Appointment Invoice API] - 2026-01-10

### Added
- **Appointment Invoice Entity** (`appointment_invoice_entity.py`)
  - AppointmentInvoice model with full tax breakdown (CGST/SGST/IGST/CESS)
  - AppointmentInvoiceItem model with line-level tax calculations
  - Generated columns for total_tax_amount and balance_amount
  - Denormalized patient and doctor information for invoice records

- **Appointment Invoice Schema** (`appointment_invoice_schema.py`)
  - AppointmentInvoiceCreateSchema with validation
  - AppointmentInvoiceUpdateSchema for partial updates
  - AppointmentInvoiceItemSchema for line items
  - Status enums: AppointmentInvoiceStatus, AppointmentInvoicePaymentStatus

- **Appointment Invoice Service** (`appointment_invoice_service.py`)
  - create(): Creates invoice with items and updates appointment table in same transaction
  - get_by_id(): Retrieves invoice with items and appointment details
  - get_all(): Paginated list with filtering by patient, doctor, appointment, status
  - update(): Updates invoice fields
  - delete(): Soft delete invoice
  - Automatic voucher creation when status is POSTED
  - Transaction-safe appointment status update (appointment_invoice_generated, appointment_invoice_id)

- **Appointment Invoice Routes** (`appointment_invoices_route.py`)
  - POST /api/v1/health/appointment-invoices - Create invoice
  - GET /api/v1/health/appointment-invoices/{id} - Get by ID with optional barcode
  - GET /api/v1/health/appointment-invoices - List with pagination and filters
  - PUT /api/v1/health/appointment-invoices/{id} - Update invoice
  - DELETE /api/v1/health/appointment-invoices/{id} - Soft delete

### Changed
- Updated appointments.sql schema with invoice tracking fields (already present)
- Registered appointment_invoices_route in main.py health routes section
- Added appointment_invoices_route to health_routes __init__.py

### Technical Details
- Invoice creation validates appointment exists and not already invoiced
- Single transaction ensures appointment table updated atomically with invoice creation
- Follows same pattern as test_invoice implementation
- Supports Indian GST compliance with split tax calculations
- Includes barcode/QR code generation support
