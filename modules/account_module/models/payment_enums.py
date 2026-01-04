from enum import Enum


class PaymentType(str, Enum):
    """Payment type enumeration"""
    RECEIPT = "RECEIPT"
    PAYMENT = "PAYMENT"
    CONTRA = "CONTRA"


class PartyType(str, Enum):
    """Party type enumeration"""
    CUSTOMER = "CUSTOMER"
    SUPPLIER = "SUPPLIER"
    EMPLOYEE = "EMPLOYEE"
    BANK = "BANK"
    PATIENT = "PATIENT"
    OTHER = "OTHER"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"
    RECONCILED = "RECONCILED"


class PaymentMode(str, Enum):
    """Payment mode enumeration"""
    CASH = "CASH"
    BANK = "BANK"
    CARD = "CARD"
    UPI = "UPI"
    CHEQUE = "CHEQUE"
    ONLINE = "ONLINE"
    WALLET = "WALLET"
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"


class DocumentType(str, Enum):
    """Document type enumeration"""
    ORDER = "ORDER"
    INVOICE = "INVOICE"
    EXPENSE = "EXPENSE"
    BILL = "BILL"
    ADVANCE = "ADVANCE"
    DEBIT_NOTE = "DEBIT_NOTE"
    CREDIT_NOTE = "CREDIT_NOTE"
    OTHER = "OTHER"
