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


## [Public Test Results API] - 2026-01-11

### Added
- **Crypto Utility** (`core/shared/utils/crypto_utils.py`)
  - CryptoUtils class for encrypting/decrypting sensitive data
  - Uses Fernet symmetric encryption with SECRET_KEY from environment
  - encrypt() method returns base64 encoded encrypted string
  - decrypt() method returns decrypted string or None on failure

- **Test Result Service Enhancement** (`test_result_service.py`)
  - get_by_result_number(): Fetches test result by result_number with barcode from test_order
  - Joins TestResult with TestOrder to retrieve barcode_data
  - Public access method without tenant_id filtering

- **Public Test Results Route** (`api/v1/routers/public_routes/test_results_public_route.py`)
  - GET /api/public/v1/health/test-results/{encrypted_result_no}
  - Decrypts encrypted result_no to get actual result_number
  - Returns test result details with barcode_data, details, and files
  - No authentication required (public endpoint)
  - Tagged as "public" in Swagger documentation

### Changed
- Updated main.py to register public routes without authentication dependency
- Added cryptography>=41.0.0 to requirements.txt

### Technical Details
- Encryption uses Fernet (symmetric encryption) with 32-byte key derived from SECRET_KEY
- Barcode data retrieved from test_orders.barcode_data (generated column = test_order_number)
- Public endpoint allows external systems to access test results via encrypted links
- Error handling for invalid/expired encrypted tokens returns 400 Bad Request


### Changed (2026-01-11)
- **Test Result Service** (`test_result_service.py`)
  - get_by_id() now generates and attaches QR code from test_order_number
  - QR code generated using BarcodeGenerator.generate_qr_code()
  - Returns base64 encoded QR code image in response

- **Test Results Route** (`testresults_route.py`)
  - GET /api/v1/health/testresults/{result_id} now includes qr_code field in response

- QR code now contains full URL: WEB_APP_URL + "/public/health/test-result/" + encrypted_result_no
- Uses crypto_utils to encrypt result_number for secure public access
- WEB_APP_URL read from environment variable (defaults to http://localhost:3000)
