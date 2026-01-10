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
