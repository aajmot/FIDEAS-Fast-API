from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal


class PaymentDetailInput(BaseModel):
    """Schema for payment detail when creating sales invoice"""
    line_no: int = Field(..., ge=1, description="Line number")
    payment_mode: str = Field(..., description="Payment mode")
    bank_account_id: Optional[int] = Field(None, description="Bank account ID")
    instrument_number: Optional[str] = Field(None, max_length=50, description="Cheque/DD number")
    instrument_date: Optional[date] = Field(None, description="Instrument date")
    bank_name: Optional[str] = Field(None, max_length=100, description="Bank name")
    branch_name: Optional[str] = Field(None, max_length=100, description="Branch name")
    ifsc_code: Optional[str] = Field(None, max_length=20, description="IFSC code")
    transaction_reference: Optional[str] = Field(None, max_length=100, description="UPI/NEFT reference")
    amount_base: Decimal = Field(..., gt=0, description="Amount in base currency")
    amount_foreign: Optional[Decimal] = Field(None, description="Amount in foreign currency")
    account_id: int = Field(..., description="Account ID for payment")
    description: Optional[str] = Field(None, description="Description")
    
    @validator('payment_mode')
    def validate_payment_mode(cls, v):
        """Validate payment mode"""
        valid_modes = {'CASH', 'BANK', 'CARD', 'UPI', 'CHEQUE', 'ONLINE', 'WALLET'}
        if v not in valid_modes:
            raise ValueError(f'Payment mode must be one of: {", ".join(valid_modes)}')
        return v
    
    class Config:
        from_attributes = True


class SalesInvoiceItemRequest(BaseModel):
    """Schema for sales invoice line item"""
    line_no: int = Field(..., ge=1, description="Line number")
    product_id: int = Field(..., description="Product ID")
    description: Optional[str] = Field(None, description="Item description")
    hsn_code: Optional[str] = Field(None, max_length=20, description="HSN code")
    batch_number: Optional[str] = Field(None, max_length=50, description="Batch number")
    serial_numbers: Optional[str] = Field(None, description="Serial numbers (comma-separated)")
    
    # Quantity
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    free_quantity: Decimal = Field(0, ge=0, description="Free/complimentary quantity")
    uom: str = Field("NOS", max_length=20, description="Unit of measurement")
    
    # Pricing (Base Currency)
    unit_price_base: Decimal = Field(..., ge=0, description="Unit price in base currency")
    unit_cost_base: Decimal = Field(..., ge=0, description="Unit cost for COGS calculation")
    discount_percent: Decimal = Field(0, ge=0, le=100, description="Discount percentage")
    discount_amount_base: Decimal = Field(0, ge=0, description="Discount amount")
    taxable_amount_base: Decimal = Field(..., ge=0, description="Taxable amount")
    
    # GST Components (No UGST for sales)
    cgst_rate: Decimal = Field(0, ge=0, le=100, description="CGST rate")
    cgst_amount_base: Decimal = Field(0, ge=0, description="CGST amount")
    sgst_rate: Decimal = Field(0, ge=0, le=100, description="SGST rate")
    sgst_amount_base: Decimal = Field(0, ge=0, description="SGST amount")
    igst_rate: Decimal = Field(0, ge=0, le=100, description="IGST rate")
    igst_amount_base: Decimal = Field(0, ge=0, description="IGST amount")
    cess_rate: Decimal = Field(0, ge=0, le=100, description="CESS rate")
    cess_amount_base: Decimal = Field(0, ge=0, description="CESS amount")
    tax_amount_base: Decimal = Field(0, ge=0, description="Total tax amount")
    
    # Total
    total_amount_base: Decimal = Field(..., ge=0, description="Total line amount")
    
    # Foreign Currency (Optional)
    unit_price_foreign: Optional[Decimal] = Field(None, description="Unit price in foreign currency")
    discount_amount_foreign: Optional[Decimal] = Field(None, description="Discount in foreign currency")
    taxable_amount_foreign: Optional[Decimal] = Field(None, description="Taxable amount in foreign currency")
    tax_amount_foreign: Optional[Decimal] = Field(None, description="Tax in foreign currency")
    total_amount_foreign: Optional[Decimal] = Field(None, description="Total in foreign currency")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "line_no": 1,
                "product_id": 1,
                "quantity": 10,
                "free_quantity": 1,
                "unit_price_base": 150.00,
                "unit_cost_base": 100.00,
                "taxable_amount_base": 1500.00,
                "cgst_rate": 9,
                "cgst_amount_base": 135.00,
                "sgst_rate": 9,
                "sgst_amount_base": 135.00,
                "tax_amount_base": 270.00,
                "total_amount_base": 1770.00
            }
        }


class SalesInvoiceItemResponse(BaseModel):
    """Schema for sales invoice item response"""
    id: int
    line_no: int
    product_id: int
    description: Optional[str] = None
    hsn_code: Optional[str] = None
    batch_number: Optional[str] = None
    serial_numbers: Optional[str] = None
    quantity: Decimal
    free_quantity: Decimal
    uom: str
    unit_price_base: Decimal
    unit_cost_base: Decimal
    discount_percent: Decimal
    discount_amount_base: Decimal
    taxable_amount_base: Decimal
    cgst_rate: Decimal
    cgst_amount_base: Decimal
    sgst_rate: Decimal
    sgst_amount_base: Decimal
    igst_rate: Decimal
    igst_amount_base: Decimal
    cess_rate: Decimal
    cess_amount_base: Decimal
    tax_amount_base: Decimal
    total_amount_base: Decimal
    unit_price_foreign: Optional[Decimal] = None
    discount_amount_foreign: Optional[Decimal] = None
    taxable_amount_foreign: Optional[Decimal] = None
    tax_amount_foreign: Optional[Decimal] = None
    total_amount_foreign: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


class SalesInvoiceRequest(BaseModel):
    """Schema for creating/updating sales invoice"""
    invoice_number: str = Field(..., max_length=50, description="Invoice number")
    reference_number: Optional[str] = Field(None, max_length=50, description="Customer PO number")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    
    # References
    customer_id: int = Field(..., description="Customer ID")
    sales_order_id: Optional[int] = Field(None, description="Sales order ID")
    payment_term_id: Optional[int] = Field(None, description="Payment term ID")
    warehouse_id: int = Field(..., description="Warehouse ID")
    shipping_address_id: Optional[int] = Field(None, description="Shipping address ID")
    
    # Currency
    base_currency_id: Optional[int] = Field(None, description="Base currency ID (defaults to INR)")
    foreign_currency_id: Optional[int] = Field(None, description="Foreign currency ID")
    exchange_rate: Decimal = Field(1, gt=0, description="Exchange rate")
    
    # GST Summary (Base Currency)
    cgst_amount_base: Decimal = Field(0, ge=0, description="Total CGST")
    sgst_amount_base: Decimal = Field(0, ge=0, description="Total SGST")
    igst_amount_base: Decimal = Field(0, ge=0, description="Total IGST")
    cess_amount_base: Decimal = Field(0, ge=0, description="Total CESS")
    
    # Totals (Base Currency)
    subtotal_base: Decimal = Field(0, ge=0, description="Subtotal")
    discount_amount_base: Decimal = Field(0, ge=0, description="Discount amount")
    tax_amount_base: Decimal = Field(0, ge=0, description="Total tax")
    total_amount_base: Decimal = Field(..., gt=0, description="Total amount")
    
    # Totals (Foreign Currency)
    subtotal_foreign: Optional[Decimal] = Field(None, description="Subtotal in foreign currency")
    discount_amount_foreign: Optional[Decimal] = Field(None, description="Discount in foreign currency")
    tax_amount_foreign: Optional[Decimal] = Field(None, description="Tax in foreign currency")
    total_amount_foreign: Optional[Decimal] = Field(None, description="Total in foreign currency")
    
    # Payment
    paid_amount_base: Decimal = Field(0, ge=0, description="Paid amount")
    balance_amount_base: Decimal = Field(0, ge=0, description="Balance amount")
    
    # Status
    status: str = Field("DRAFT", description="Invoice status")
    invoice_type: str = Field("TAX_INVOICE", description="Invoice type")
    
    # e-Invoice fields
    is_einvoice: bool = Field(False, description="Generate e-Invoice")
    
    # e-Way Bill fields  
    generate_eway_bill: bool = Field(False, description="Generate e-Way Bill")
    
    # Metadata
    notes: Optional[str] = Field(None, description="Notes")
    terms_conditions: Optional[str] = Field(None, description="Terms and conditions")
    tags: Optional[List[str]] = Field(None, description="Tags")
    
    # Items
    items: List[SalesInvoiceItemRequest] = Field(..., min_length=1, description="Invoice items")
    
    # Payment Details (Optional - if provided, payment will be created)
    payment_details: Optional[List[PaymentDetailInput]] = Field(None, description="Payment details for immediate payment")
    payment_number: Optional[str] = Field(None, max_length=50, description="Payment number (if making payment)")
    payment_remarks: Optional[str] = Field(None, description="Payment remarks")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "invoice_number": "SINV-2025-001",
                "reference_number": "CUST-PO-123",
                "invoice_date": "2025-01-15",
                "due_date": "2025-02-14",
                "customer_id": 1,
                "warehouse_id": 1,
                "exchange_rate": 1,
                "subtotal_base": 15000.00,
                "tax_amount_base": 2700.00,
                "total_amount_base": 17700.00,
                "status": "DRAFT",
                "invoice_type": "TAX_INVOICE",
                "is_einvoice": False,
                "generate_eway_bill": False,
                "items": [
                    {
                        "line_no": 1,
                        "product_id": 1,
                        "description": "Product description",
                        "hsn_code": "1234",
                        "quantity": 10,
                        "free_quantity": 1,
                        "uom": "NOS",
                        "unit_price_base": 150.00,
                        "unit_cost_base": 100.00,
                        "discount_percent": 0,
                        "discount_amount_base": 0,
                        "taxable_amount_base": 1500.00,
                        "cgst_rate": 9,
                        "cgst_amount_base": 135.00,
                        "sgst_rate": 9,
                        "sgst_amount_base": 135.00,
                        "igst_rate": 0,
                        "igst_amount_base": 0,
                        "cess_rate": 0,
                        "cess_amount_base": 0,
                        "tax_amount_base": 270.00,
                        "total_amount_base": 1770.00
                    }
                ]
            }
        }
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status values"""
        valid_statuses = {'DRAFT', 'POSTED', 'PAID', 'PARTIALLY_PAID', 'CANCELLED', 'CREDIT_NOTE'}
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    @validator('invoice_type')
    def validate_invoice_type(cls, v):
        """Validate invoice type values"""
        valid_types = {'TAX_INVOICE', 'BILL_OF_SUPPLY', 'EXPORT', 'CREDIT_NOTE'}
        if v not in valid_types:
            raise ValueError(f'Invoice type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Ensure due date is not before invoice date"""
        if v and 'invoice_date' in values and v < values['invoice_date']:
            raise ValueError('Due date cannot be before invoice date')
        return v
    
    @validator('foreign_currency_id')
    def validate_foreign_currency(cls, v, values):
        """Validate foreign currency logic"""
        if v is None:
            # No foreign currency - ensure exchange rate is 1
            if values.get('exchange_rate', 1) != 1:
                raise ValueError('Exchange rate must be 1 when no foreign currency')
        else:
            # Has foreign currency - ensure exchange rate is positive
            if values.get('exchange_rate', 0) <= 0:
                raise ValueError('Exchange rate must be positive when foreign currency is set')
        return v


class SalesInvoiceResponse(BaseModel):
    """Schema for sales invoice response"""
    id: int
    invoice_number: str
    reference_number: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    sales_order_id: Optional[int] = None
    payment_term_id: Optional[int] = None
    warehouse_id: int
    shipping_address_id: Optional[int] = None
    base_currency_id: int
    foreign_currency_id: Optional[int] = None
    exchange_rate: Decimal
    cgst_amount_base: Decimal
    sgst_amount_base: Decimal
    igst_amount_base: Decimal
    cess_amount_base: Decimal
    subtotal_base: Decimal
    discount_amount_base: Decimal
    tax_amount_base: Decimal
    total_amount_base: Decimal
    subtotal_foreign: Optional[Decimal] = None
    discount_amount_foreign: Optional[Decimal] = None
    tax_amount_foreign: Optional[Decimal] = None
    total_amount_foreign: Optional[Decimal] = None
    paid_amount_base: Decimal
    balance_amount_base: Decimal
    status: str
    invoice_type: str
    is_einvoice: bool
    einvoice_irn: Optional[str] = None
    einvoice_ack_no: Optional[str] = None
    einvoice_ack_date: Optional[datetime] = None
    einvoice_qr_code: Optional[str] = None
    einvoice_status: str
    eway_bill_no: Optional[str] = None
    eway_bill_date: Optional[datetime] = None
    eway_bill_valid_till: Optional[datetime] = None
    voucher_id: Optional[int] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    tags: Optional[List[str]] = None
    payments: Optional[List[dict]] = []
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    is_active: bool
    is_deleted: bool
    items: List[SalesInvoiceItemResponse] = []
    
    class Config:
        from_attributes = True


class SalesInvoiceListResponse(BaseModel):
    """Schema for paginated list of sales invoices"""
    total: int
    page: int
    per_page: int
    total_pages: int
    data: List[SalesInvoiceResponse]
    
    class Config:
        from_attributes = True


class EInvoiceGenerateRequest(BaseModel):
    """Schema for e-Invoice generation request"""
    invoice_id: int = Field(..., description="Sales invoice ID")
    
    class Config:
        from_attributes = True


class EInvoiceGenerateResponse(BaseModel):
    """Schema for e-Invoice generation response"""
    success: bool
    irn: str = Field(..., description="Invoice Reference Number")
    ack_no: str = Field(..., description="Acknowledgement Number")
    ack_date: datetime
    qr_code: str = Field(..., description="QR Code data")
    message: Optional[str] = None
    
    class Config:
        from_attributes = True


class EWayBillGenerateRequest(BaseModel):
    """Schema for e-Way Bill generation request"""
    invoice_id: int = Field(..., description="Sales invoice ID")
    transporter_id: Optional[int] = Field(None, description="Transporter ID")
    vehicle_number: Optional[str] = Field(None, max_length=20, description="Vehicle number")
    transport_mode: str = Field(..., description="Transport mode (ROAD/RAIL/AIR/SHIP)")
    distance: Decimal = Field(..., gt=0, description="Distance in KM")
    
    @validator('transport_mode')
    def validate_transport_mode(cls, v):
        """Validate transport mode"""
        valid_modes = {'ROAD', 'RAIL', 'AIR', 'SHIP'}
        if v not in valid_modes:
            raise ValueError(f'Transport mode must be one of: {", ".join(valid_modes)}')
        return v
    
    class Config:
        from_attributes = True


class EWayBillGenerateResponse(BaseModel):
    """Schema for e-Way Bill generation response"""
    success: bool
    eway_bill_no: str = Field(..., description="e-Way Bill Number")
    eway_bill_date: datetime
    valid_till: datetime
    message: Optional[str] = None
    
    class Config:
        from_attributes = True
