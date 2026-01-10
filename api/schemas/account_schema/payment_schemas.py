from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
from decimal import Decimal
from enum import Enum


class InvoiceType(str, Enum):
    PURCHASE = 'PURCHASE'
    SALES = 'SALES'
    TEST = 'TEST'
    CLINIC = 'CLINIC'
    EXPENSE = 'EXPENSE'
    BILL = 'BILL'
    ADVANCE = 'ADVANCE'
    DEBIT_NOTE = 'DEBIT_NOTE'
    CREDIT_NOTE = 'CREDIT_NOTE'


class PaymentMode(str, Enum):
    CASH = 'CASH'
    CHEQUE = 'CHEQUE'
    BANK = 'BANK'
    UPI = 'UPI'
    ONLINE = 'ONLINE'
    CARD = 'CARD'
    WALLET = 'WALLET'
    NEFT = 'NEFT'
    RTGS = 'RTGS'
    IMPS = 'IMPS'


class PartyType(str, Enum):
    CUSTOMER = 'CUSTOMER'
    SUPPLIER = 'SUPPLIER'
    PATIENT = 'PATIENT'
    EMPLOYEE = 'EMPLOYEE'

class PaymentStatus(str, Enum):
    DRAFT = 'DRAFT'
    POSTED = 'POSTED'
    CANCELLED = 'CANCELLED'    


class InvoicePaymentRequest(BaseModel):
    payment_number: str = Field(..., max_length=50, description="Payment number")
    invoice_id: int = Field(..., description="Invoice ID")
    invoice_type: InvoiceType = Field(..., description="Invoice type")
    party_name: str = Field(..., max_length=200, description="Party name")
    party_phone: str = Field(..., max_length=20, description="Party phone")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_mode: PaymentMode = Field(PaymentMode.CASH, description="Payment mode")
    instrument_number: Optional[str] = Field(None, description="Cheque/DD number")
    instrument_date: Optional[date] = Field(None, description="Instrument date")
    bank_name: Optional[str] = Field(None, description="Bank name")
    branch_name: Optional[str] = Field(None, description="Branch name")
    ifsc_code: Optional[str] = Field(None, description="IFSC code")
    transaction_reference: Optional[str] = Field(None, description="Transaction reference")
    remarks: Optional[str] = Field(None, description="Remarks")


class AdvancePaymentRequest(BaseModel):
    payment_number: str = Field(..., max_length=50, description="Payment number")
    party_id: int = Field(..., description="Party ID")
    party_type: PartyType = Field(..., description="Party type")
    party_name: str = Field(..., max_length=200, description="Party name")
    party_phone: str = Field(..., max_length=20, description="Party phone")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_mode: PaymentMode = Field(PaymentMode.CASH, description="Payment mode")
    instrument_number: Optional[str] = Field(None, description="Cheque/DD number")
    instrument_date: Optional[date] = Field(None, description="Instrument date")
    bank_name: Optional[str] = Field(None, description="Bank name")
    branch_name: Optional[str] = Field(None, description="Branch name")
    ifsc_code: Optional[str] = Field(None, description="IFSC code")
    transaction_reference: Optional[str] = Field(None, description="Transaction reference")
    remarks: Optional[str] = Field(None, description="Remarks")


class GatewayPaymentUpdateRequest(BaseModel):
    transaction_reference: str = Field(..., description="UPI/Gateway transaction reference")
    gateway_transaction_id: Optional[str] = Field(None, description="Gateway transaction ID")
    gateway_status: str = Field(..., description="Gateway status (SUCCESS/FAILED)")
    gateway_fee_base: Optional[Decimal] = Field(0, description="Gateway fee")
    gateway_response: Optional[str] = Field(None, description="Gateway response JSON")
    
    @validator('gateway_status')
    def validate_status(cls, v):
        if v not in ['SUCCESS', 'FAILED']:
            raise ValueError('gateway_status must be SUCCESS or FAILED')
        return v


class PaymentMetadataUpdate(BaseModel):
    remarks: Optional[str] = Field(None, description="Remarks")
    tags: Optional[list[str]] = Field(None, description="Tags")
    reference_number: Optional[str] = Field(None, max_length=50, description="Reference number")


class PaymentReversalRequest(BaseModel):
    reversal_date: Optional[date] = Field(None, description="Reversal date")
    reversal_remarks: str = Field(..., description="Reason for reversal")
