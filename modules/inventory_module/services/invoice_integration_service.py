from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from modules.inventory_module.services.sales_invoice_service import SalesInvoiceService
from modules.inventory_module.services.purchase_invoice_service import PurchaseInvoiceService
from modules.account_module.services.payment_service import PaymentService
from modules.inventory_module.services.stock_service import StockService
from decimal import Decimal
from datetime import datetime


class InvoiceIntegrationService:
    """Integration service for invoice processing with enhanced payment and stock handling"""
    
    def __init__(self):
        self.sales_invoice_service = SalesInvoiceService()
        self.purchase_invoice_service = PurchaseInvoiceService()
        self.payment_service = PaymentService()
        self.stock_service = StockService()
    
    @ExceptionMiddleware.handle_exceptions("InvoiceIntegrationService")
    def create_sales_invoice_with_payment(self, invoice_data: dict):
        """Create sales invoice with integrated payment handling and proper status alignment"""
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                # Extract payment information
                payment_details = invoice_data.pop('payment_details', None)
                payment_number = invoice_data.pop('payment_number', None)
                payment_remarks = invoice_data.pop('payment_remarks', None)
                
                # Calculate payment amount
                paid_amount = Decimal('0.0000')
                if payment_details:
                    paid_amount = sum(Decimal(str(detail.get('amount_base', 0))) for detail in payment_details)
                
                # Set proper status based on payment alignment
                total_amount = Decimal(str(invoice_data.get('total_amount_base', 0)))
                if paid_amount >= total_amount:
                    invoice_data['status'] = 'PAID'
                elif paid_amount > 0:
                    invoice_data['status'] = 'PARTIALLY_PAID'
                else:
                    invoice_data['status'] = 'POSTED'
                
                # Update payment amounts in invoice
                invoice_data['paid_amount_base'] = paid_amount
                invoice_data['balance_amount_base'] = total_amount - paid_amount
                
                # Create the sales invoice (this handles stock transactions and voucher creation)
                invoice_result = self.sales_invoice_service.create(invoice_data)
                
                # Create separate payment if payment details provided
                payment_result = None
                if payment_details and payment_number and paid_amount > 0:
                    payment_data = {
                        'payment_number': payment_number,
                        'payment_date': datetime.utcnow(),
                        'payment_type': 'RECEIPT',
                        'party_type': 'CUSTOMER',
                        'party_id': invoice_data.get('customer_id'),
                        'base_currency_id': invoice_data.get('base_currency_id'),
                        'foreign_currency_id': invoice_data.get('foreign_currency_id'),
                        'exchange_rate': invoice_data.get('exchange_rate', 1),
                        'total_amount_base': paid_amount,
                        'total_amount_foreign': paid_amount * Decimal(str(invoice_data.get('exchange_rate', 1))) if invoice_data.get('foreign_currency_id') else None,
                        'reference_number': invoice_result.get('invoice_number'),
                        'remarks': payment_remarks or f"Receipt for invoice {invoice_result.get('invoice_number')}",
                        'details': payment_details
                    }
                    
                    payment_result = self.payment_service.create_invoice_payment(payment_data)
                
                # Combine results
                result = invoice_result.copy()
                if payment_result:
                    result['payment'] = payment_result
                
                return result
                
            except Exception as e:
                session.rollback()
                raise
    
    @ExceptionMiddleware.handle_exceptions("InvoiceIntegrationService")
    def create_purchase_invoice_with_payment(self, invoice_data: dict):
        """Create purchase invoice with integrated payment handling and proper status alignment"""
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                # Extract payment information
                payment_details = invoice_data.pop('payment_details', None)
                payment_number = invoice_data.pop('payment_number', None)
                payment_remarks = invoice_data.pop('payment_remarks', None)
                
                # Calculate payment amount
                paid_amount = Decimal('0.0000')
                if payment_details:
                    paid_amount = sum(Decimal(str(detail.get('amount_base', 0))) for detail in payment_details)
                
                # Set proper status based on payment alignment
                total_amount = Decimal(str(invoice_data.get('total_amount_base', 0)))
                if paid_amount >= total_amount:
                    invoice_data['status'] = 'PAID'
                elif paid_amount > 0:
                    invoice_data['status'] = 'PARTIALLY_PAID'
                else:
                    invoice_data['status'] = 'POSTED'
                
                # Update payment amounts in invoice
                invoice_data['paid_amount_base'] = paid_amount
                invoice_data['balance_amount_base'] = total_amount - paid_amount
                
                # Create the purchase invoice (this handles stock transactions and voucher creation)
                invoice_result = self.purchase_invoice_service.create(invoice_data)
                
                # Create separate payment if payment details provided
                payment_result = None
                if payment_details and payment_number and paid_amount > 0:
                    payment_data = {
                        'payment_number': payment_number,
                        'payment_date': datetime.utcnow(),
                        'payment_type': 'PAYMENT',
                        'party_type': 'SUPPLIER',
                        'party_id': invoice_data.get('supplier_id'),
                        'base_currency_id': invoice_data.get('base_currency_id'),
                        'foreign_currency_id': invoice_data.get('foreign_currency_id'),
                        'exchange_rate': invoice_data.get('exchange_rate', 1),
                        'total_amount_base': paid_amount,
                        'total_amount_foreign': paid_amount * Decimal(str(invoice_data.get('exchange_rate', 1))) if invoice_data.get('foreign_currency_id') else None,
                        'reference_number': invoice_result.get('invoice_number'),
                        'remarks': payment_remarks or f"Payment for invoice {invoice_result.get('invoice_number')}",
                        'details': payment_details
                    }
                    
                    payment_result = self.payment_service.create_invoice_payment(payment_data)
                
                # Combine results
                result = invoice_result.copy()
                if payment_result:
                    result['payment'] = payment_result
                
                return result
                
            except Exception as e:
                session.rollback()
                raise
    
    @ExceptionMiddleware.handle_exceptions("InvoiceIntegrationService")
    def process_invoice_payment(self, invoice_type: str, invoice_id: int, payment_data: dict):
        """Process payment for existing invoice with proper status updates"""
        try:
            # Create the payment
            payment_result = self.payment_service.create_invoice_payment(payment_data)
            
            # Update invoice payment status
            payment_amount = payment_data.get('total_amount_base', 0)
            status_result = self.payment_service.update_invoice_payment_status(
                invoice_type, invoice_id, payment_amount
            )
            
            return {
                'payment': payment_result,
                'invoice_status': status_result
            }
            
        except Exception as e:
            raise
    
    @ExceptionMiddleware.handle_exceptions("InvoiceIntegrationService")
    def get_invoice_payment_summary(self, invoice_type: str, invoice_id: int):
        """Get comprehensive payment summary for an invoice"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            if invoice_type == 'SALES':
                from modules.inventory_module.models.sales_invoice_entity import SalesInvoice
                invoice = session.query(SalesInvoice).filter(
                    SalesInvoice.id == invoice_id,
                    SalesInvoice.tenant_id == tenant_id,
                    SalesInvoice.is_deleted == False
                ).first()
                party_type = 'CUSTOMER'
                party_id = invoice.customer_id if invoice else None
            elif invoice_type == 'PURCHASE':
                from modules.inventory_module.models.purchase_invoice_entity import PurchaseInvoice
                invoice = session.query(PurchaseInvoice).filter(
                    PurchaseInvoice.id == invoice_id,
                    PurchaseInvoice.tenant_id == tenant_id,
                    PurchaseInvoice.is_deleted == False
                ).first()
                party_type = 'SUPPLIER'
                party_id = invoice.supplier_id if invoice else None
            else:
                raise ValueError(f"Unsupported invoice type: {invoice_type}")
            
            if not invoice:
                raise ValueError(f"{invoice_type} invoice with ID {invoice_id} not found")
            
            # Get all payments for this invoice
            from modules.account_module.models.payment_entity import Payment
            payments = session.query(Payment).filter(
                Payment.party_type == party_type,
                Payment.party_id == party_id,
                Payment.reference_number == invoice.invoice_number,
                Payment.tenant_id == tenant_id,
                Payment.is_deleted == False
            ).all()
            
            # Calculate payment summary
            total_payments = sum(float(p.total_amount_base or 0) for p in payments)
            
            return {
                'invoice_id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'invoice_type': invoice_type,
                'total_amount': float(invoice.total_amount_base or 0),
                'paid_amount': float(invoice.paid_amount_base or 0),
                'balance_amount': float(invoice.balance_amount_base or 0),
                'status': invoice.status,
                'payment_count': len(payments),
                'payments': [
                    {
                        'payment_id': p.id,
                        'payment_number': p.payment_number,
                        'payment_date': p.payment_date.isoformat() if p.payment_date else None,
                        'amount': float(p.total_amount_base or 0),
                        'status': p.status
                    }
                    for p in payments
                ]
            }
    
    @ExceptionMiddleware.handle_exceptions("InvoiceIntegrationService")
    def validate_free_quantity_stock_impact(self, items_data: list):
        """Validate that free quantities don't exceed available stock"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            validation_results = []
            
            for item in items_data:
                product_id = item.get('product_id')
                batch_number = item.get('batch_number', '')
                paid_qty = float(item.get('quantity', 0))
                free_qty = float(item.get('free_quantity', 0))
                total_qty = paid_qty + free_qty
                
                # Get current stock balance
                from modules.inventory_module.models.stock_entity import StockBalance
                balance = session.query(StockBalance).filter(
                    StockBalance.product_id == product_id,
                    StockBalance.batch_number == batch_number,
                    StockBalance.tenant_id == tenant_id
                ).first()
                
                available_qty = float(balance.available_quantity or 0) if balance else 0
                
                validation_results.append({
                    'product_id': product_id,
                    'batch_number': batch_number,
                    'paid_quantity': paid_qty,
                    'free_quantity': free_qty,
                    'total_required': total_qty,
                    'available_stock': available_qty,
                    'sufficient_stock': available_qty >= total_qty,
                    'shortage': max(0, total_qty - available_qty)
                })
            
            return {
                'valid': all(item['sufficient_stock'] for item in validation_results),
                'items': validation_results
            }