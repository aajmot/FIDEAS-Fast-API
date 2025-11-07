from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from modules.inventory_module.models.purchase_invoice_entity import PurchaseInvoice, PurchaseInvoiceItem
from modules.account_module.models.entities import Voucher, VoucherLine, VoucherType
from modules.account_module.models.account_configuration_entity import AccountConfiguration
from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey
from modules.account_module.models.payment_entity import Payment, PaymentDetail
from sqlalchemy import func, or_
from decimal import Decimal
from datetime import datetime
import math


class PurchaseInvoiceService:
    """Service layer for purchase invoice management"""
    
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
    
    @ExceptionMiddleware.handle_exceptions("PurchaseInvoiceService")
    def create(self, invoice_data: dict):
        """Create a new purchase invoice with items, voucher, and optional payment in a single transaction"""
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                # Check if invoice number already exists
                existing = session.query(PurchaseInvoice).filter(
                    PurchaseInvoice.tenant_id == tenant_id,
                    PurchaseInvoice.invoice_number == invoice_data.get('invoice_number'),
                    PurchaseInvoice.is_deleted == False
                ).first()
                
                if existing:
                    raise ValueError(f"Invoice number '{invoice_data.get('invoice_number')}' already exists")
                
                # Extract items and payment details from invoice data
                items_data = invoice_data.pop('items', [])
                payment_details_data = invoice_data.pop('payment_details', None)
                payment_number = invoice_data.pop('payment_number', None)
                payment_remarks = invoice_data.pop('payment_remarks', None)
                
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
                invoice = PurchaseInvoice(
                    tenant_id=tenant_id,
                    invoice_number=invoice_data.get('invoice_number'),
                    reference_number=invoice_data.get('reference_number'),
                    invoice_date=invoice_data.get('invoice_date'),
                    due_date=invoice_data.get('due_date'),
                    supplier_id=invoice_data.get('supplier_id'),
                    purchase_order_id=invoice_data.get('purchase_order_id'),
                    payment_term_id=invoice_data.get('payment_term_id'),
                    warehouse_id=invoice_data.get('warehouse_id'),
                    base_currency_id=invoice_data.get('base_currency_id'),
                    foreign_currency_id=invoice_data.get('foreign_currency_id'),
                    exchange_rate=exchange_rate,
                    cgst_amount_base=invoice_data.get('cgst_amount_base', 0),
                    sgst_amount_base=invoice_data.get('sgst_amount_base', 0),
                    igst_amount_base=invoice_data.get('igst_amount_base', 0),
                    ugst_amount_base=invoice_data.get('ugst_amount_base', 0),
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
                    notes=invoice_data.get('notes'),
                    tags=invoice_data.get('tags'),
                    created_by=username,
                    updated_by=username
                )
                
                session.add(invoice)
                session.flush()  # Get invoice ID
                
                # Create invoice items
                for item_data in items_data:
                    item = PurchaseInvoiceItem(
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
                        discount_percent=item_data.get('discount_percent', 0),
                        discount_amount_base=item_data.get('discount_amount_base', 0),
                        taxable_amount_base=item_data.get('taxable_amount_base'),
                        cgst_rate=item_data.get('cgst_rate', 0),
                        cgst_amount_base=item_data.get('cgst_amount_base', 0),
                        sgst_rate=item_data.get('sgst_rate', 0),
                        sgst_amount_base=item_data.get('sgst_amount_base', 0),
                        igst_rate=item_data.get('igst_rate', 0),
                        igst_amount_base=item_data.get('igst_amount_base', 0),
                        ugst_rate=item_data.get('ugst_rate', 0),
                        ugst_amount_base=item_data.get('ugst_amount_base', 0),
                        cess_rate=item_data.get('cess_rate', 0),
                        cess_amount_base=item_data.get('cess_amount_base', 0),
                        tax_amount_base=item_data.get('tax_amount_base', 0),
                        total_amount_base=item_data.get('total_amount_base'),
                        unit_price_foreign=item_data.get('unit_price_foreign'),
                        discount_amount_foreign=item_data.get('discount_amount_foreign'),
                        taxable_amount_foreign=item_data.get('taxable_amount_foreign'),
                        tax_amount_foreign=item_data.get('tax_amount_foreign'),
                        total_amount_foreign=item_data.get('total_amount_foreign'),
                        landed_cost_per_unit=item_data.get('landed_cost_per_unit'),
                        created_by=username,
                        updated_by=username
                    )
                    session.add(item)
                
                # Create accounting voucher for the purchase invoice
                voucher = self._create_purchase_voucher(
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
    
    def _create_purchase_voucher(self, session, tenant_id, username, invoice, items_data):
        """Create accounting voucher for purchase invoice"""
        # Get or create Purchase voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.tenant_id == tenant_id,
            VoucherType.code == 'PURCHASE',
            VoucherType.is_active == True,
            VoucherType.is_deleted == False
        ).first()
        
        if not voucher_type:
            raise ValueError("Purchase voucher type not configured. Please configure 'PURCHASE' voucher type.")
        
        # Generate voucher number
        voucher_number = f"PV-{invoice.invoice_number}"
        
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
            reference_type='PURCHASE_INVOICE',
            reference_id=invoice.id,
            reference_number=invoice.invoice_number,
            narration=f"Purchase invoice {invoice.invoice_number} from supplier {invoice.supplier_id}",
            is_posted=True,
            created_by=username,
            updated_by=username
        )
        
        session.add(voucher)
        session.flush()
        
        # Get configured account IDs
        try:
            purchase_account_id = self._get_configured_account(session, tenant_id, 'PURCHASE')
            accounts_payable_id = self._get_configured_account(session, tenant_id, 'ACCOUNTS_PAYABLE')
            cgst_input_id = self._get_configured_account(session, tenant_id, 'GST_INPUT_CGST')
            sgst_input_id = self._get_configured_account(session, tenant_id, 'GST_INPUT_SGST')
            igst_input_id = self._get_configured_account(session, tenant_id, 'GST_INPUT_IGST')
        except ValueError as e:
            raise ValueError(f"Account configuration error: {str(e)}. Please run tenant accounting initialization.")
        
        # Create voucher lines
        line_no = 1
        
        # Debit: Purchase Account (or Inventory Account)
        purchase_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=line_no,
            account_id=purchase_account_id,
            description=f"Purchase - {invoice.reference_number or invoice.invoice_number}",
            debit_base=invoice.subtotal_base,
            credit_base=Decimal(0),
            debit_foreign=invoice.subtotal_foreign,
            credit_foreign=Decimal(0) if invoice.subtotal_foreign else None,
            reference_type='PURCHASE_INVOICE',
            reference_id=invoice.id,
            created_by=username,
            updated_by=username
        )
        session.add(purchase_line)
        line_no += 1
        
        # Debit: Tax Accounts (CGST, SGST, IGST, etc.)
        if invoice.cgst_amount_base > 0:
            cgst_line = VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=cgst_input_id,
                description="CGST Input",
                debit_base=invoice.cgst_amount_base,
                credit_base=Decimal(0),
                tax_amount_base=invoice.cgst_amount_base,
                reference_type='PURCHASE_INVOICE',
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
                account_id=sgst_input_id,
                description="SGST Input",
                debit_base=invoice.sgst_amount_base,
                credit_base=Decimal(0),
                tax_amount_base=invoice.sgst_amount_base,
                reference_type='PURCHASE_INVOICE',
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
                account_id=igst_input_id,
                description="IGST Input",
                debit_base=invoice.igst_amount_base,
                credit_base=Decimal(0),
                tax_amount_base=invoice.igst_amount_base,
                reference_type='PURCHASE_INVOICE',
                reference_id=invoice.id,
                created_by=username,
                updated_by=username
            )
            session.add(igst_line)
            line_no += 1
        
        # Credit: Supplier Account (Accounts Payable)
        supplier_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=line_no,
            account_id=accounts_payable_id,
            description=f"Supplier {invoice.supplier_id}",
            debit_base=Decimal(0),
            credit_base=invoice.total_amount_base,
            debit_foreign=Decimal(0) if invoice.total_amount_foreign else None,
            credit_foreign=invoice.total_amount_foreign,
            reference_type='PURCHASE_INVOICE',
            reference_id=invoice.id,
            created_by=username,
            updated_by=username
        )
        session.add(supplier_line)
        
        return voucher
    
    def _create_payment(self, session, tenant_id, username, invoice, payment_number, payment_details_data, payment_remarks):
        """Create payment record for the purchase invoice"""
        # Calculate total payment amount
        total_payment = sum(Decimal(str(detail.get('amount_base', 0))) for detail in payment_details_data)
        
        # Create payment header
        payment = Payment(
            tenant_id=tenant_id,
            payment_number=payment_number,
            payment_date=datetime.utcnow(),
            payment_type='PAYMENT',
            party_type='SUPPLIER',
            party_id=invoice.supplier_id,
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
    
    @ExceptionMiddleware.handle_exceptions("PurchaseInvoiceService")
    def get_all(self, page=1, page_size=100, search=None, status=None, supplier_id=None, 
                date_from=None, date_to=None):
        """Get all purchase invoices with pagination and filters"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            )
            
            # Apply filters
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        PurchaseInvoice.invoice_number.ilike(search_pattern),
                        PurchaseInvoice.reference_number.ilike(search_pattern)
                    )
                )
            
            if status:
                query = query.filter(PurchaseInvoice.status == status)
            
            if supplier_id:
                query = query.filter(PurchaseInvoice.supplier_id == supplier_id)
            
            if date_from:
                query = query.filter(PurchaseInvoice.invoice_date >= date_from)
            
            if date_to:
                query = query.filter(PurchaseInvoice.invoice_date <= date_to)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            query = query.order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.id.desc())
            offset = (page - 1) * page_size
            invoices = query.offset(offset).limit(page_size).all()
            
            return {
                'total': total,
                'page': page,
                'per_page': page_size,
                'total_pages': math.ceil(total / page_size) if total > 0 else 0,
                'data': [self._to_dict(inv, include_items=False) for inv in invoices]
            }
    
    @ExceptionMiddleware.handle_exceptions("PurchaseInvoiceService")
    def get_by_id(self, invoice_id: int):
        """Get a specific purchase invoice by ID with items"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            invoice = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                return None
            
            return self._to_dict(invoice, include_items=True)
    
    @ExceptionMiddleware.handle_exceptions("PurchaseInvoiceService")
    def update(self, invoice_id: int, invoice_data: dict):
        """Update an existing purchase invoice"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            invoice = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                return None
            
            # Check if invoice number changed and is unique
            if 'invoice_number' in invoice_data and invoice_data['invoice_number'] != invoice.invoice_number:
                existing = session.query(PurchaseInvoice).filter(
                    PurchaseInvoice.tenant_id == tenant_id,
                    PurchaseInvoice.invoice_number == invoice_data['invoice_number'],
                    PurchaseInvoice.id != invoice_id,
                    PurchaseInvoice.is_deleted == False
                ).first()
                
                if existing:
                    raise ValueError(f"Invoice number '{invoice_data['invoice_number']}' already exists")
            
            # Extract items if present
            items_data = invoice_data.pop('items', None)
            
            # Update header fields
            for field in ['invoice_number', 'reference_number', 'invoice_date', 'due_date',
                         'supplier_id', 'purchase_order_id', 'payment_term_id', 'warehouse_id',
                         'base_currency_id', 'foreign_currency_id', 'exchange_rate',
                         'cgst_amount_base', 'sgst_amount_base', 'igst_amount_base', 
                         'ugst_amount_base', 'cess_amount_base',
                         'subtotal_base', 'discount_amount_base', 'tax_amount_base', 'total_amount_base',
                         'subtotal_foreign', 'discount_amount_foreign', 'tax_amount_foreign', 'total_amount_foreign',
                         'paid_amount_base', 'balance_amount_base', 'status', 'notes', 'tags']:
                if field in invoice_data:
                    setattr(invoice, field, invoice_data[field])
            
            invoice.updated_by = username
            
            # Update items if provided
            if items_data is not None:
                # Delete existing items
                session.query(PurchaseInvoiceItem).filter(
                    PurchaseInvoiceItem.invoice_id == invoice_id
                ).delete()
                
                # Add new items
                for item_data in items_data:
                    item = PurchaseInvoiceItem(
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
                        discount_percent=item_data.get('discount_percent', 0),
                        discount_amount_base=item_data.get('discount_amount_base', 0),
                        taxable_amount_base=item_data.get('taxable_amount_base'),
                        cgst_rate=item_data.get('cgst_rate', 0),
                        cgst_amount_base=item_data.get('cgst_amount_base', 0),
                        sgst_rate=item_data.get('sgst_rate', 0),
                        sgst_amount_base=item_data.get('sgst_amount_base', 0),
                        igst_rate=item_data.get('igst_rate', 0),
                        igst_amount_base=item_data.get('igst_amount_base', 0),
                        ugst_rate=item_data.get('ugst_rate', 0),
                        ugst_amount_base=item_data.get('ugst_amount_base', 0),
                        cess_rate=item_data.get('cess_rate', 0),
                        cess_amount_base=item_data.get('cess_amount_base', 0),
                        tax_amount_base=item_data.get('tax_amount_base', 0),
                        total_amount_base=item_data.get('total_amount_base'),
                        unit_price_foreign=item_data.get('unit_price_foreign'),
                        discount_amount_foreign=item_data.get('discount_amount_foreign'),
                        taxable_amount_foreign=item_data.get('taxable_amount_foreign'),
                        tax_amount_foreign=item_data.get('tax_amount_foreign'),
                        total_amount_foreign=item_data.get('total_amount_foreign'),
                        landed_cost_per_unit=item_data.get('landed_cost_per_unit'),
                        created_by=username,
                        updated_by=username
                    )
                    session.add(item)
            
            session.commit()
            session.refresh(invoice)
            
            return self.get_by_id(invoice.id)
    
    @ExceptionMiddleware.handle_exceptions("PurchaseInvoiceService")
    def delete(self, invoice_id: int):
        """Soft delete a purchase invoice"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            invoice = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                return False
            
            # Check if invoice can be deleted (only DRAFT or CANCELLED)
            if invoice.status not in ['DRAFT', 'CANCELLED']:
                raise ValueError(f"Cannot delete invoice with status '{invoice.status}'. Only DRAFT or CANCELLED invoices can be deleted.")
            
            invoice.is_deleted = True
            invoice.is_active = False
            invoice.updated_by = username
            
            session.commit()
            return True
    
    @ExceptionMiddleware.handle_exceptions("PurchaseInvoiceService")
    def update_payment(self, invoice_id: int, payment_amount: Decimal):
        """Update payment information for an invoice"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            invoice = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                return None
            
            # Update paid amount and balance
            invoice.paid_amount_base += payment_amount
            invoice.balance_amount_base = invoice.total_amount_base - invoice.paid_amount_base
            
            # Update status based on payment
            if invoice.balance_amount_base <= 0:
                invoice.status = 'PAID'
            elif invoice.paid_amount_base > 0:
                invoice.status = 'PARTIALLY_PAID'
            
            invoice.updated_by = username
            
            session.commit()
            session.refresh(invoice)
            
            return self._to_dict(invoice, include_items=False)
    
    def _to_dict(self, invoice, include_items=True):
        """Convert invoice entity to dictionary"""
        result = {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'reference_number': invoice.reference_number,
            'invoice_date': invoice.invoice_date,
            'due_date': invoice.due_date,
            'supplier_id': invoice.supplier_id,
            'purchase_order_id': invoice.purchase_order_id,
            'payment_term_id': invoice.payment_term_id,
            'warehouse_id': invoice.warehouse_id,
            'base_currency_id': invoice.base_currency_id,
            'foreign_currency_id': invoice.foreign_currency_id,
            'exchange_rate': invoice.exchange_rate,
            'cgst_amount_base': invoice.cgst_amount_base,
            'sgst_amount_base': invoice.sgst_amount_base,
            'igst_amount_base': invoice.igst_amount_base,
            'ugst_amount_base': invoice.ugst_amount_base,
            'cess_amount_base': invoice.cess_amount_base,
            'subtotal_base': invoice.subtotal_base,
            'discount_amount_base': invoice.discount_amount_base,
            'tax_amount_base': invoice.tax_amount_base,
            'total_amount_base': invoice.total_amount_base,
            'subtotal_foreign': invoice.subtotal_foreign,
            'discount_amount_foreign': invoice.discount_amount_foreign,
            'tax_amount_foreign': invoice.tax_amount_foreign,
            'total_amount_foreign': invoice.total_amount_foreign,
            'paid_amount_base': invoice.paid_amount_base,
            'balance_amount_base': invoice.balance_amount_base,
            'status': invoice.status,
            'voucher_id': invoice.voucher_id,
            'notes': invoice.notes,
            'tags': invoice.tags,
            'created_at': invoice.created_at,
            'created_by': invoice.created_by,
            'updated_at': invoice.updated_at,
            'updated_by': invoice.updated_by,
            'is_active': invoice.is_active,
            'is_deleted': invoice.is_deleted
        }
        
        if include_items:
            result['items'] = [self._item_to_dict(item) for item in invoice.invoice_items]
        else:
            result['items'] = []
        
        return result
    
    def _item_to_dict(self, item):
        """Convert invoice item entity to dictionary"""
        return {
            'id': item.id,
            'line_no': item.line_no,
            'product_id': item.product_id,
            'description': item.description,
            'hsn_code': item.hsn_code,
            'batch_number': item.batch_number,
            'serial_numbers': item.serial_numbers,
            'quantity': item.quantity,
            'uom': item.uom,
            'unit_price_base': item.unit_price_base,
            'discount_percent': item.discount_percent,
            'discount_amount_base': item.discount_amount_base,
            'taxable_amount_base': item.taxable_amount_base,
            'cgst_rate': item.cgst_rate,
            'cgst_amount_base': item.cgst_amount_base,
            'sgst_rate': item.sgst_rate,
            'sgst_amount_base': item.sgst_amount_base,
            'igst_rate': item.igst_rate,
            'igst_amount_base': item.igst_amount_base,
            'ugst_rate': item.ugst_rate,
            'ugst_amount_base': item.ugst_amount_base,
            'cess_rate': item.cess_rate,
            'cess_amount_base': item.cess_amount_base,
            'tax_amount_base': item.tax_amount_base,
            'total_amount_base': item.total_amount_base,
            'unit_price_foreign': item.unit_price_foreign,
            'discount_amount_foreign': item.discount_amount_foreign,
            'taxable_amount_foreign': item.taxable_amount_foreign,
            'tax_amount_foreign': item.tax_amount_foreign,
            'total_amount_foreign': item.total_amount_foreign,
            'landed_cost_per_unit': item.landed_cost_per_unit
        }
