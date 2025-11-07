from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from modules.inventory_module.models.sales_invoice_entity import SalesInvoice, SalesInvoiceItem
from modules.account_module.models.entities import Voucher, VoucherLine, VoucherType
from modules.account_module.models.account_configuration_entity import AccountConfiguration
from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey
from modules.account_module.models.payment_entity import Payment, PaymentDetail
from sqlalchemy import func, or_
from decimal import Decimal
from datetime import datetime
import math


class SalesInvoiceService:
    """Service layer for sales invoice management"""
    
    def _get_default_currency_id(self, session, tenant_id):
        """Get default currency ID for tenant (defaults to INR if not configured)"""
        from modules.admin_module.models.currency_entity import Currency
        
        # Try to get tenant's default currency from settings
        # For now, default to INR (currency code 'INR')
        currency = session.query(Currency).filter(
            Currency.code == 'INR',
            Currency.is_active == True
        ).first()
        
        if not currency:
            # If INR not found, get any active currency
            currency = session.query(Currency).filter(
                Currency.is_active == True
            ).first()
        
        if not currency:
            raise ValueError("No active currency found. Please configure currencies.")
        
        return currency.id
    
    def _get_configured_account(self, session, tenant_id, config_code):
        """Get configured account ID for a given configuration code"""
        # Get configuration key
        config_key = session.query(AccountConfigurationKey).filter(
            AccountConfigurationKey.code == config_code,
            AccountConfigurationKey.is_active == True,
            AccountConfigurationKey.is_deleted == False
        ).first()
        
        if not config_key:
            raise ValueError(f"Account configuration key '{config_code}' not found")
        
        # Get tenant-specific configuration
        config = session.query(AccountConfiguration).filter(
            AccountConfiguration.tenant_id == tenant_id,
            AccountConfiguration.config_key_id == config_key.id,
            AccountConfiguration.is_deleted == False
        ).first()
        
        if not config:
            # Fallback to default account if tenant config not found
            if config_key.default_account_id:
                return config_key.default_account_id
            raise ValueError(f"Account configuration for '{config_code}' not found for tenant {tenant_id}")
        
        return config.account_id
    
    @ExceptionMiddleware.handle_exceptions("SalesInvoiceService")
    def create(self, invoice_data: dict):
        """Create a new sales invoice with items, voucher, and optional payment in a single transaction"""
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                # Check if invoice number already exists
                existing = session.query(SalesInvoice).filter(
                    SalesInvoice.tenant_id == tenant_id,
                    SalesInvoice.invoice_number == invoice_data.get('invoice_number'),
                    SalesInvoice.is_deleted == False
                ).first()
                
                if existing:
                    raise ValueError(f"Invoice number '{invoice_data.get('invoice_number')}' already exists")
                
                # Extract items and payment details from invoice data
                items_data = invoice_data.pop('items', [])
                payment_details_data = invoice_data.pop('payment_details', None)
                payment_number = invoice_data.pop('payment_number', None)
                payment_remarks = invoice_data.pop('payment_remarks', None)
                generate_eway_bill = invoice_data.pop('generate_eway_bill', False)
                
                # Calculate paid amount from payment details if provided
                paid_amount = Decimal(0)
                if payment_details_data:
                    paid_amount = sum(Decimal(str(detail.get('amount_base', 0))) for detail in payment_details_data)
                
                # Update invoice paid_amount and balance_amount
                total_amount = Decimal(str(invoice_data.get('total_amount_base')))
                invoice_data['paid_amount_base'] = paid_amount
                invoice_data['balance_amount_base'] = total_amount - paid_amount
                
                # Update status based on payment
                if paid_amount >= total_amount:
                    invoice_data['status'] = 'PAID'
                elif paid_amount > 0:
                    invoice_data['status'] = 'PARTIALLY_PAID'
                elif invoice_data.get('status') == 'DRAFT':
                    invoice_data['status'] = 'POSTED'
                
                # Set default currency if not provided
                if not invoice_data.get('base_currency_id'):
                    invoice_data['base_currency_id'] = self._get_default_currency_id(session, tenant_id)
                
                # Set exchange rate to 1 if not provided
                exchange_rate = invoice_data.get('exchange_rate')
                if exchange_rate is None or exchange_rate == '':
                    exchange_rate = Decimal('1')
                else:
                    exchange_rate = Decimal(str(exchange_rate))
                
                # Set paid and balance amounts as Decimal
                paid_amount = Decimal(str(paid_amount))
                balance_amount = Decimal(str(invoice_data['balance_amount_base']))
                
                # Create invoice header
                invoice = SalesInvoice(
                    tenant_id=tenant_id,
                    invoice_number=invoice_data.get('invoice_number'),
                    reference_number=invoice_data.get('reference_number'),
                    invoice_date=invoice_data.get('invoice_date'),
                    due_date=invoice_data.get('due_date'),
                    customer_id=invoice_data.get('customer_id'),
                    sales_order_id=invoice_data.get('sales_order_id'),
                    payment_term_id=invoice_data.get('payment_term_id'),
                    warehouse_id=invoice_data.get('warehouse_id'),
                    shipping_address_id=invoice_data.get('shipping_address_id'),
                    base_currency_id=invoice_data.get('base_currency_id'),
                    foreign_currency_id=invoice_data.get('foreign_currency_id'),
                    exchange_rate=exchange_rate,
                    cgst_amount_base=invoice_data.get('cgst_amount_base', 0),
                    sgst_amount_base=invoice_data.get('sgst_amount_base', 0),
                    igst_amount_base=invoice_data.get('igst_amount_base', 0),
                    cess_amount_base=invoice_data.get('cess_amount_base', 0),
                    subtotal_base=invoice_data.get('subtotal_base', 0),
                    discount_amount_base=invoice_data.get('discount_amount_base', 0),
                    tax_amount_base=invoice_data.get('tax_amount_base', 0),
                    total_amount_base=total_amount,
                    subtotal_foreign=invoice_data.get('subtotal_foreign'),
                    discount_amount_foreign=invoice_data.get('discount_amount_foreign'),
                    tax_amount_foreign=invoice_data.get('tax_amount_foreign'),
                    total_amount_foreign=invoice_data.get('total_amount_foreign'),
                    paid_amount_base=paid_amount,
                    balance_amount_base=balance_amount,
                    status=invoice_data['status'],
                    invoice_type=invoice_data.get('invoice_type', 'TAX_INVOICE'),
                    is_einvoice=invoice_data.get('is_einvoice', False),
                    einvoice_status='PENDING' if invoice_data.get('is_einvoice', False) else 'PENDING',
                    notes=invoice_data.get('notes'),
                    terms_conditions=invoice_data.get('terms_conditions'),
                    tags=invoice_data.get('tags'),
                    created_by=username,
                    updated_by=username
                )
                
                session.add(invoice)
                session.flush()  # Get invoice ID
                
                # Create invoice items
                for item_data in items_data:
                    item = SalesInvoiceItem(
                        tenant_id=tenant_id,
                        invoice_id=invoice.id,
                        line_no=item_data.get('line_no'),
                        product_id=item_data.get('product_id'),
                        description=item_data.get('description'),
                        hsn_code=item_data.get('hsn_code'),
                        batch_number=item_data.get('batch_number'),
                        serial_numbers=item_data.get('serial_numbers'),
                        quantity=item_data.get('quantity'),
                        uom=item_data.get('uom', 'NOS'),
                        unit_price_base=item_data.get('unit_price_base'),
                        unit_cost_base=item_data.get('unit_cost_base'),
                        discount_percent=item_data.get('discount_percent', 0),
                        discount_amount_base=item_data.get('discount_amount_base', 0),
                        taxable_amount_base=item_data.get('taxable_amount_base'),
                        cgst_rate=item_data.get('cgst_rate', 0),
                        cgst_amount_base=item_data.get('cgst_amount_base', 0),
                        sgst_rate=item_data.get('sgst_rate', 0),
                        sgst_amount_base=item_data.get('sgst_amount_base', 0),
                        igst_rate=item_data.get('igst_rate', 0),
                        igst_amount_base=item_data.get('igst_amount_base', 0),
                        cess_rate=item_data.get('cess_rate', 0),
                        cess_amount_base=item_data.get('cess_amount_base', 0),
                        tax_amount_base=item_data.get('tax_amount_base', 0),
                        total_amount_base=item_data.get('total_amount_base'),
                        unit_price_foreign=item_data.get('unit_price_foreign'),
                        discount_amount_foreign=item_data.get('discount_amount_foreign'),
                        taxable_amount_foreign=item_data.get('taxable_amount_foreign'),
                        tax_amount_foreign=item_data.get('tax_amount_foreign'),
                        total_amount_foreign=item_data.get('total_amount_foreign'),
                        created_by=username,
                        updated_by=username
                    )
                    session.add(item)
                
                # Create accounting voucher for the sales invoice
                voucher = self._create_sales_voucher(
                    session=session,
                    tenant_id=tenant_id,
                    username=username,
                    invoice=invoice,
                    items_data=items_data
                )
                
                # Link voucher to invoice
                invoice.voucher_id = voucher.id
                
                # Create payment if payment details provided
                payment = None
                if payment_details_data and payment_number:
                    payment = self._create_payment(
                        session=session,
                        tenant_id=tenant_id,
                        username=username,
                        invoice=invoice,
                        payment_number=payment_number,
                        payment_details_data=payment_details_data,
                        payment_remarks=payment_remarks
                    )
                
                session.commit()
                session.refresh(invoice)
                
                result = self.get_by_id(invoice.id)
                
                # Add payment info to result if payment was created
                if payment:
                    result['payment_id'] = payment.id
                    result['payment_number'] = payment.payment_number
                
                return result
                
            except Exception as e:
                session.rollback()
                raise
    
    def _create_sales_voucher(self, session, tenant_id, username, invoice, items_data):
        """Create accounting voucher for sales invoice"""
        # Get or create Sales voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.tenant_id == tenant_id,
            VoucherType.code == 'SALES',
            VoucherType.is_active == True,
            VoucherType.is_deleted == False
        ).first()
        
        if not voucher_type:
            raise ValueError("Sales voucher type not configured. Please configure 'SALES' voucher type.")
        
        # Generate voucher number
        voucher_number = f"SV-{invoice.invoice_number}"
        
        # Create voucher
        voucher = Voucher(
            tenant_id=tenant_id,
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=invoice.invoice_date if hasattr(invoice.invoice_date, 'hour') else datetime.combine(invoice.invoice_date, datetime.min.time()),
            base_currency_id=invoice.base_currency_id,
            foreign_currency_id=invoice.foreign_currency_id,
            exchange_rate=invoice.exchange_rate,
            base_total_amount=invoice.total_amount_base,
            base_total_debit=invoice.total_amount_base,
            base_total_credit=invoice.total_amount_base,
            foreign_total_amount=invoice.total_amount_foreign,
            foreign_total_debit=invoice.total_amount_foreign,
            foreign_total_credit=invoice.total_amount_foreign,
            reference_type='SALES_INVOICE',
            reference_id=invoice.id,
            reference_number=invoice.invoice_number,
            narration=f"Sales invoice {invoice.invoice_number} to customer {invoice.customer_id}",
            is_posted=True,
            created_by=username,
            updated_by=username
        )
        
        session.add(voucher)
        session.flush()
        
        # Get configured account IDs
        try:
            sales_account_id = self._get_configured_account(session, tenant_id, 'SALES')
            accounts_receivable_id = self._get_configured_account(session, tenant_id, 'ACCOUNTS_RECEIVABLE')
            cgst_output_id = self._get_configured_account(session, tenant_id, 'GST_OUTPUT_CGST')
            sgst_output_id = self._get_configured_account(session, tenant_id, 'GST_OUTPUT_SGST')
            igst_output_id = self._get_configured_account(session, tenant_id, 'GST_OUTPUT_IGST')
        except ValueError as e:
            raise ValueError(f"Account configuration error: {str(e)}. Please run tenant accounting initialization.")
        
        # Create voucher lines
        line_no = 1
        
        # Debit: Customer Account (Accounts Receivable)
        customer_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=line_no,
            account_id=accounts_receivable_id,
            description=f"Customer {invoice.customer_id}",
            debit_base=invoice.total_amount_base,
            credit_base=Decimal(0),
            debit_foreign=invoice.total_amount_foreign,
            credit_foreign=Decimal(0) if invoice.total_amount_foreign else None,
            reference_type='SALES_INVOICE',
            reference_id=invoice.id,
            created_by=username,
            updated_by=username
        )
        session.add(customer_line)
        line_no += 1
        
        # Credit: Sales Account
        sales_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=line_no,
            account_id=sales_account_id,
            description=f"Sales - {invoice.reference_number or invoice.invoice_number}",
            debit_base=Decimal(0),
            credit_base=invoice.subtotal_base,
            debit_foreign=Decimal(0) if invoice.subtotal_foreign else None,
            credit_foreign=invoice.subtotal_foreign,
            reference_type='SALES_INVOICE',
            reference_id=invoice.id,
            created_by=username,
            updated_by=username
        )
        session.add(sales_line)
        line_no += 1
        
        # Credit: Tax Accounts (CGST, SGST, IGST, etc.)
        if invoice.cgst_amount_base > 0:
            cgst_line = VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=cgst_output_id,
                description="CGST Output",
                debit_base=Decimal(0),
                credit_base=invoice.cgst_amount_base,
                tax_amount_base=invoice.cgst_amount_base,
                reference_type='SALES_INVOICE',
                reference_id=invoice.id,
                created_by=username,
                updated_by=username
            )
            session.add(cgst_line)
            line_no += 1
        
        if invoice.sgst_amount_base > 0:
            sgst_line = VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=sgst_output_id,
                description="SGST Output",
                debit_base=Decimal(0),
                credit_base=invoice.sgst_amount_base,
                tax_amount_base=invoice.sgst_amount_base,
                reference_type='SALES_INVOICE',
                reference_id=invoice.id,
                created_by=username,
                updated_by=username
            )
            session.add(sgst_line)
            line_no += 1
        
        if invoice.igst_amount_base > 0:
            igst_line = VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=igst_output_id,
                description="IGST Output",
                debit_base=Decimal(0),
                credit_base=invoice.igst_amount_base,
                tax_amount_base=invoice.igst_amount_base,
                reference_type='SALES_INVOICE',
                reference_id=invoice.id,
                created_by=username,
                updated_by=username
            )
            session.add(igst_line)
            line_no += 1
        
        return voucher
    
    def _create_payment(self, session, tenant_id, username, invoice, payment_number, payment_details_data, payment_remarks):
        """Create payment record for the sales invoice"""
        # Calculate total payment amount
        total_payment = sum(Decimal(str(detail.get('amount_base', 0))) for detail in payment_details_data)
        
        # Create payment header
        payment = Payment(
            tenant_id=tenant_id,
            payment_number=payment_number,
            payment_date=datetime.utcnow(),
            payment_type='RECEIPT',
            party_type='CUSTOMER',
            party_id=invoice.customer_id,
            base_currency_id=invoice.base_currency_id,
            foreign_currency_id=invoice.foreign_currency_id,
            exchange_rate=invoice.exchange_rate,
            total_amount_base=total_payment,
            total_amount_foreign=total_payment * invoice.exchange_rate if invoice.foreign_currency_id else None,
            status='POSTED',
            reference_number=invoice.invoice_number,
            remarks=payment_remarks or f"Payment for invoice {invoice.invoice_number}",
            created_by=username,
            updated_by=username
        )
        
        session.add(payment)
        session.flush()
        
        # Create payment details
        for detail_data in payment_details_data:
            detail = PaymentDetail(
                tenant_id=tenant_id,
                payment_id=payment.id,
                line_no=detail_data.get('line_no'),
                payment_mode=detail_data.get('payment_mode'),
                bank_account_id=detail_data.get('bank_account_id'),
                instrument_number=detail_data.get('instrument_number'),
                instrument_date=detail_data.get('instrument_date'),
                bank_name=detail_data.get('bank_name'),
                branch_name=detail_data.get('branch_name'),
                ifsc_code=detail_data.get('ifsc_code'),
                transaction_reference=detail_data.get('transaction_reference'),
                amount_base=detail_data.get('amount_base'),
                amount_foreign=detail_data.get('amount_foreign'),
                account_id=detail_data.get('account_id'),
                description=detail_data.get('description'),
                created_by=username,
                updated_by=username
            )
            session.add(detail)
        
        return payment
    
    @ExceptionMiddleware.handle_exceptions("SalesInvoiceService")
    def get_all(self, page=1, page_size=100, search=None, status=None, customer_id=None, 
                date_from=None, date_to=None, invoice_type=None):
        """Get all sales invoices with pagination and filters"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(SalesInvoice).filter(
                SalesInvoice.tenant_id == tenant_id,
                SalesInvoice.is_deleted == False
            )
            
            # Apply filters
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        SalesInvoice.invoice_number.ilike(search_pattern),
                        SalesInvoice.reference_number.ilike(search_pattern)
                    )
                )
            
            if status:
                query = query.filter(SalesInvoice.status == status)
            
            if customer_id:
                query = query.filter(SalesInvoice.customer_id == customer_id)
            
            if invoice_type:
                query = query.filter(SalesInvoice.invoice_type == invoice_type)
            
            if date_from:
                query = query.filter(SalesInvoice.invoice_date >= date_from)
            
            if date_to:
                query = query.filter(SalesInvoice.invoice_date <= date_to)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            query = query.order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.id.desc())
            offset = (page - 1) * page_size
            invoices = query.offset(offset).limit(page_size).all()
            
            return {
                'total': total,
                'page': page,
                'per_page': page_size,
                'total_pages': math.ceil(total / page_size) if total > 0 else 0,
                'data': [self._to_dict(inv, include_items=False) for inv in invoices]
            }
    
    @ExceptionMiddleware.handle_exceptions("SalesInvoiceService")
    def get_by_id(self, invoice_id: int):
        """Get a specific sales invoice by ID with items"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            invoice = session.query(SalesInvoice).filter(
                SalesInvoice.id == invoice_id,
                SalesInvoice.tenant_id == tenant_id,
                SalesInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                raise ValueError(f"Sales invoice with ID {invoice_id} not found")
            
            return self._to_dict(invoice, include_items=True)
    
    @ExceptionMiddleware.handle_exceptions("SalesInvoiceService")
    def update(self, invoice_id: int, invoice_data: dict):
        """Update an existing sales invoice"""
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                invoice = session.query(SalesInvoice).filter(
                    SalesInvoice.id == invoice_id,
                    SalesInvoice.tenant_id == tenant_id,
                    SalesInvoice.is_deleted == False
                ).first()
                
                if not invoice:
                    raise ValueError(f"Sales invoice with ID {invoice_id} not found")
                
                # Cannot update posted/paid invoices
                if invoice.status not in ['DRAFT']:
                    raise ValueError(f"Cannot update invoice with status {invoice.status}")
                
                # Extract items from invoice data
                items_data = invoice_data.pop('items', None)
                
                # Update invoice fields
                for key, value in invoice_data.items():
                    if hasattr(invoice, key) and key not in ['id', 'tenant_id', 'created_at', 'created_by']:
                        setattr(invoice, key, value)
                
                invoice.updated_by = username
                invoice.updated_at = datetime.utcnow()
                
                # Update items if provided
                if items_data is not None:
                    # Delete existing items
                    session.query(SalesInvoiceItem).filter(
                        SalesInvoiceItem.invoice_id == invoice_id
                    ).delete()
                    
                    # Create new items
                    for item_data in items_data:
                        item = SalesInvoiceItem(
                            tenant_id=tenant_id,
                            invoice_id=invoice.id,
                            **item_data,
                            created_by=username,
                            updated_by=username
                        )
                        session.add(item)
                
                session.commit()
                session.refresh(invoice)
                
                return self.get_by_id(invoice_id)
                
            except Exception as e:
                session.rollback()
                raise
    
    @ExceptionMiddleware.handle_exceptions("SalesInvoiceService")
    def delete(self, invoice_id: int):
        """Soft delete a sales invoice"""
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                invoice = session.query(SalesInvoice).filter(
                    SalesInvoice.id == invoice_id,
                    SalesInvoice.tenant_id == tenant_id,
                    SalesInvoice.is_deleted == False
                ).first()
                
                if not invoice:
                    raise ValueError(f"Sales invoice with ID {invoice_id} not found")
                
                # Cannot delete posted/paid invoices
                if invoice.status not in ['DRAFT', 'CANCELLED']:
                    raise ValueError(f"Cannot delete invoice with status {invoice.status}. Please cancel it first.")
                
                invoice.is_deleted = True
                invoice.updated_by = username
                invoice.updated_at = datetime.utcnow()
                
                session.commit()
                
                return {"message": "Sales invoice deleted successfully"}
                
            except Exception as e:
                session.rollback()
                raise
    
    def _to_dict(self, invoice, include_items=True):
        """Convert invoice entity to dictionary"""
        result = {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'reference_number': invoice.reference_number,
            'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'customer_id': invoice.customer_id,
            'sales_order_id': invoice.sales_order_id,
            'payment_term_id': invoice.payment_term_id,
            'warehouse_id': invoice.warehouse_id,
            'shipping_address_id': invoice.shipping_address_id,
            'base_currency_id': invoice.base_currency_id,
            'foreign_currency_id': invoice.foreign_currency_id,
            'exchange_rate': float(invoice.exchange_rate) if invoice.exchange_rate else 1.0,
            'cgst_amount_base': float(invoice.cgst_amount_base) if invoice.cgst_amount_base else 0.0,
            'sgst_amount_base': float(invoice.sgst_amount_base) if invoice.sgst_amount_base else 0.0,
            'igst_amount_base': float(invoice.igst_amount_base) if invoice.igst_amount_base else 0.0,
            'cess_amount_base': float(invoice.cess_amount_base) if invoice.cess_amount_base else 0.0,
            'subtotal_base': float(invoice.subtotal_base) if invoice.subtotal_base else 0.0,
            'discount_amount_base': float(invoice.discount_amount_base) if invoice.discount_amount_base else 0.0,
            'tax_amount_base': float(invoice.tax_amount_base) if invoice.tax_amount_base else 0.0,
            'total_amount_base': float(invoice.total_amount_base) if invoice.total_amount_base else 0.0,
            'subtotal_foreign': float(invoice.subtotal_foreign) if invoice.subtotal_foreign else None,
            'discount_amount_foreign': float(invoice.discount_amount_foreign) if invoice.discount_amount_foreign else None,
            'tax_amount_foreign': float(invoice.tax_amount_foreign) if invoice.tax_amount_foreign else None,
            'total_amount_foreign': float(invoice.total_amount_foreign) if invoice.total_amount_foreign else None,
            'paid_amount_base': float(invoice.paid_amount_base) if invoice.paid_amount_base else 0.0,
            'balance_amount_base': float(invoice.balance_amount_base) if invoice.balance_amount_base else 0.0,
            'status': invoice.status,
            'invoice_type': invoice.invoice_type,
            'is_einvoice': invoice.is_einvoice,
            'einvoice_irn': invoice.einvoice_irn,
            'einvoice_ack_no': invoice.einvoice_ack_no,
            'einvoice_ack_date': invoice.einvoice_ack_date.isoformat() if invoice.einvoice_ack_date else None,
            'einvoice_qr_code': invoice.einvoice_qr_code,
            'einvoice_status': invoice.einvoice_status,
            'eway_bill_no': invoice.eway_bill_no,
            'eway_bill_date': invoice.eway_bill_date.isoformat() if invoice.eway_bill_date else None,
            'eway_bill_valid_till': invoice.eway_bill_valid_till.isoformat() if invoice.eway_bill_valid_till else None,
            'voucher_id': invoice.voucher_id,
            'notes': invoice.notes,
            'terms_conditions': invoice.terms_conditions,
            'tags': invoice.tags,
            'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
            'created_by': invoice.created_by,
            'updated_at': invoice.updated_at.isoformat() if invoice.updated_at else None,
            'updated_by': invoice.updated_by,
            'is_active': invoice.is_active,
            'is_deleted': invoice.is_deleted
        }
        
        if include_items and hasattr(invoice, 'invoice_items'):
            result['items'] = [
                {
                    'id': item.id,
                    'line_no': item.line_no,
                    'product_id': item.product_id,
                    'description': item.description,
                    'hsn_code': item.hsn_code,
                    'batch_number': item.batch_number,
                    'serial_numbers': item.serial_numbers,
                    'quantity': float(item.quantity) if item.quantity else 0.0,
                    'uom': item.uom,
                    'unit_price_base': float(item.unit_price_base) if item.unit_price_base else 0.0,
                    'unit_cost_base': float(item.unit_cost_base) if item.unit_cost_base else 0.0,
                    'discount_percent': float(item.discount_percent) if item.discount_percent else 0.0,
                    'discount_amount_base': float(item.discount_amount_base) if item.discount_amount_base else 0.0,
                    'taxable_amount_base': float(item.taxable_amount_base) if item.taxable_amount_base else 0.0,
                    'cgst_rate': float(item.cgst_rate) if item.cgst_rate else 0.0,
                    'cgst_amount_base': float(item.cgst_amount_base) if item.cgst_amount_base else 0.0,
                    'sgst_rate': float(item.sgst_rate) if item.sgst_rate else 0.0,
                    'sgst_amount_base': float(item.sgst_amount_base) if item.sgst_amount_base else 0.0,
                    'igst_rate': float(item.igst_rate) if item.igst_rate else 0.0,
                    'igst_amount_base': float(item.igst_amount_base) if item.igst_amount_base else 0.0,
                    'cess_rate': float(item.cess_rate) if item.cess_rate else 0.0,
                    'cess_amount_base': float(item.cess_amount_base) if item.cess_amount_base else 0.0,
                    'tax_amount_base': float(item.tax_amount_base) if item.tax_amount_base else 0.0,
                    'total_amount_base': float(item.total_amount_base) if item.total_amount_base else 0.0,
                    'unit_price_foreign': float(item.unit_price_foreign) if item.unit_price_foreign else None,
                    'discount_amount_foreign': float(item.discount_amount_foreign) if item.discount_amount_foreign else None,
                    'taxable_amount_foreign': float(item.taxable_amount_foreign) if item.taxable_amount_foreign else None,
                    'tax_amount_foreign': float(item.tax_amount_foreign) if item.tax_amount_foreign else None,
                    'total_amount_foreign': float(item.total_amount_foreign) if item.total_amount_foreign else None
                }
                for item in invoice.invoice_items
            ]
        
        return result
