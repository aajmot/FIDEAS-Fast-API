from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from modules.inventory_module.models.sales_invoice_entity import SalesInvoice, SalesInvoiceItem
from modules.account_module.models.entities import Voucher, VoucherLine, VoucherType
from modules.account_module.models.account_configuration_entity import AccountConfiguration
from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey
from modules.account_module.models.payment_entity import Payment, PaymentDetail
from modules.inventory_module.services.stock_service import StockService
from sqlalchemy import func, or_
from decimal import Decimal
from datetime import datetime
import math


class SalesInvoiceService:
    """Service layer for sales invoice management"""
    
    def _get_default_currency_id(self, session, tenant_id):
        """Get default currency ID for tenant (defaults to INR if not configured)"""
        from modules.admin_module.models.currency import Currency
        
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
        from modules.account_module.models.entities import AccountMaster
        
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
        
        account_id = None
        if config:
            account_id = config.account_id
        elif config_key.default_account_id:
            account_id = config_key.default_account_id
        else:
            raise ValueError(f"Account configuration for '{config_code}' not found for tenant {tenant_id}")
        
        # Verify the account actually exists
        account = session.query(AccountMaster).filter(
            AccountMaster.id == account_id,
            AccountMaster.tenant_id == tenant_id,
            AccountMaster.is_deleted == False
        ).first()
        
        if not account:
            # If configured account doesn't exist, try fallback for CASH/BANK
            if config_code in ['CASH', 'BANK']:
                payment_mode = config_code
                fallback_account_id = self._get_or_create_cash_bank_account(session, tenant_id, payment_mode, 'system')
                if fallback_account_id:
                    return fallback_account_id
            raise ValueError(f"Configured account ID {account_id} for '{config_code}' does not exist")
        
        return account_id
    
    def _get_or_create_cash_bank_account(self, session, tenant_id, payment_mode, username):
        """Get or create cash/bank account for payment mode"""
        from modules.account_module.models.entities import AccountMaster, AccountGroup
        
        # Try to find existing cash/bank account
        account_type = 'CASH' if payment_mode == 'CASH' else 'BANK'
        existing_account = session.query(AccountMaster).filter(
            AccountMaster.tenant_id == tenant_id,
            AccountMaster.code.ilike(f"%{account_type}%"),
            AccountMaster.account_type == 'ASSET',
            AccountMaster.is_deleted == False
        ).first()
        
        if existing_account:
            return existing_account.id
        
        # Find suitable parent group
        parent_group = session.query(AccountGroup).filter(
            AccountGroup.tenant_id == tenant_id,
            AccountGroup.account_type == 'ASSET',
            AccountGroup.is_active == True
        ).first()
        
        if not parent_group:
            return None
        
        # Create new account
        account_name = "Cash Account" if payment_mode == 'CASH' else "Bank Account"
        account_code = f"{account_type}-001"
        
        new_account = AccountMaster(
            tenant_id=tenant_id,
            account_group_id=parent_group.id,
            code=account_code,
            name=account_name,
            description=f"Default {account_name.lower()} for payments",
            account_type='ASSET',
            normal_balance='D',
            is_system_account=True,
            level=1,
            opening_balance=Decimal(0),
            current_balance=Decimal(0),
            is_active=True,
            is_deleted=False,
            created_by=username,
            updated_by=username
        )
        
        session.add(new_account)
        session.flush()
        
        return new_account.id
    
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
                
                # Validate and auto-populate account_id in payment details if missing
                if payment_details_data:
                    for detail in payment_details_data:
                        if not detail.get('account_id'):
                            payment_mode = detail.get('payment_mode', 'CASH')
                            # Auto-determine account_id based on payment mode
                            try:
                                if payment_mode == 'CASH':
                                    detail['account_id'] = self._get_configured_account(session, tenant_id, 'CASH')
                                else:
                                    detail['account_id'] = self._get_configured_account(session, tenant_id, 'BANK')
                            except ValueError:
                                # Try to create or find fallback account
                                fallback_account_id = self._get_or_create_cash_bank_account(session, tenant_id, payment_mode, username)
                                if fallback_account_id:
                                    detail['account_id'] = fallback_account_id
                                else:
                                    raise ValueError(f"Unable to determine account for payment mode {payment_mode}. Please configure CASH/BANK accounts.")
                

                generate_eway_bill = invoice_data.pop('generate_eway_bill', False)
                
                # Calculate paid amount from payment details if provided
                paid_amount = Decimal('0.0000')
                if payment_details_data:
                    paid_amount = sum(Decimal(str(detail.get('amount_base', 0))) for detail in payment_details_data)
                
                # Update invoice paid_amount and balance_amount
                total_amount = Decimal(str(invoice_data.get('total_amount_base')))
                invoice_data['paid_amount_base'] = paid_amount
                # Round balance to 2 decimal places to avoid negative tiny amounts
                invoice_data['balance_amount_base'] = (total_amount - paid_amount).quantize(Decimal('0.01'))
                
                # Update status based on payment alignment
                if paid_amount >= total_amount:
                    invoice_data['status'] = 'PAID'
                elif paid_amount > 0:
                    invoice_data['status'] = 'PARTIALLY_PAID'
                else:
                    # If no payment, set to POSTED (not DRAFT)
                    invoice_data['status'] = 'POSTED'
                
                # Set default currency if not provided
                if not invoice_data.get('base_currency_id'):
                    invoice_data['base_currency_id'] = self._get_default_currency_id(session, tenant_id)
                
                # Set exchange rate to 1 if not provided
                exchange_rate = invoice_data.get('exchange_rate')
                if exchange_rate is None or exchange_rate == '':
                    exchange_rate = Decimal('1.0000')
                else:
                    exchange_rate = Decimal(str(exchange_rate))
                
                # Ensure exchange_rate is properly set in invoice_data
                invoice_data['exchange_rate'] = exchange_rate
                
                # Convert and round all amounts to proper Decimal with 4 decimal places
                cgst_amount = Decimal(str(invoice_data.get('cgst_amount_base', 0))).quantize(Decimal('0.0001'))
                sgst_amount = Decimal(str(invoice_data.get('sgst_amount_base', 0))).quantize(Decimal('0.0001'))
                igst_amount = Decimal(str(invoice_data.get('igst_amount_base', 0))).quantize(Decimal('0.0001'))
                cess_amount = Decimal(str(invoice_data.get('cess_amount_base', 0))).quantize(Decimal('0.0001'))
                
                # Recalculate tax_amount to match sum of GST components (fixes rounding issues)
                tax_amount = (cgst_amount + sgst_amount + igst_amount + cess_amount).quantize(Decimal('0.0001'))
                
                subtotal = Decimal(str(invoice_data.get('subtotal_base', 0))).quantize(Decimal('0.0001'))
                discount_amount = Decimal(str(invoice_data.get('discount_amount_base', 0))).quantize(Decimal('0.0001'))
                
                # Recalculate total_amount = subtotal + tax_amount (subtotal should already have discount applied)
                total_amount = (subtotal + tax_amount).quantize(Decimal('0.0001'))
                
                # Update paid and balance based on the corrected total
                paid_amount = invoice_data['paid_amount_base']
                balance_amount = (total_amount - paid_amount).quantize(Decimal('0.01'))
                
                # Ensure balance doesn't go negative due to rounding (if paid >= total, set to 0)
                if balance_amount < 0 and abs(balance_amount) < Decimal('0.01'):
                    balance_amount = Decimal('0.00')
                
                # Update status based on corrected amounts - ensure proper alignment
                if balance_amount <= 0:
                    invoice_data['status'] = 'PAID'
                elif paid_amount > 0:
                    invoice_data['status'] = 'PARTIALLY_PAID'
                else:
                    invoice_data['status'] = 'POSTED'
                
                # Create invoice header with corrected amounts
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
                    cgst_amount_base=cgst_amount,
                    sgst_amount_base=sgst_amount,
                    igst_amount_base=igst_amount,
                    cess_amount_base=cess_amount,
                    subtotal_base=subtotal,
                    discount_amount_base=discount_amount,
                    tax_amount_base=tax_amount,
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
                        free_quantity=item_data.get('free_quantity', 0),
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
                
                # Flush to get item IDs for stock tracking
                session.flush()
                
                # Record stock transactions for each line item
                stock_service = StockService()
                stock_service.record_sales_invoice_transaction_in_session(
                    session=session,
                    tenant_id=tenant_id,
                    invoice_id=invoice.id,
                    invoice_number=invoice.invoice_number,
                    invoice_date=invoice.invoice_date,
                    items_data=items_data,
                    username=username
                )
                
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
                if payment_details_data:
                    # Generate payment number if not provided
                    if not payment_number:
                        payment_number = f"REC-{invoice.invoice_number}"
                    
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
    
    def _get_or_create_customer_account(self, session, tenant_id, customer_id, username):
        """Get or create account master for customer"""
        from modules.inventory_module.models.customer_entity import Customer
        from modules.account_module.models.entities import AccountMaster, AccountGroup
        
        # Get customer details
        customer = session.query(Customer).filter(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id,
            Customer.is_active == True
        ).first()
        
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")
        
        # Check if customer account already exists
        customer_account = session.query(AccountMaster).filter(
            AccountMaster.tenant_id == tenant_id,
            AccountMaster.system_code == f'CUSTOMER_{customer_id}',
            AccountMaster.is_deleted == False
        ).first()
        
        if customer_account:
            return customer_account.id
        
        # Try to get Accounts Receivable account as parent
        parent_account_id = None
        parent_group_id = None
        
        try:
            # Try to get configured Accounts Receivable account
            receivable_account_id = self._get_configured_account(session, tenant_id, 'ACCOUNTS_RECEIVABLE')
            receivable_account = session.query(AccountMaster).filter(
                AccountMaster.id == receivable_account_id,
                AccountMaster.tenant_id == tenant_id
            ).first()
            
            if receivable_account:
                parent_account_id = receivable_account.id
                parent_group_id = receivable_account.account_group_id
        except ValueError:
            # If no configured account, try to find Accounts Receivable group
            receivable_group = session.query(AccountGroup).filter(
                AccountGroup.tenant_id == tenant_id,
                AccountGroup.code.in_(['ACCOUNTS_RECEIVABLE', 'SUNDRY_DEBTORS', 'DEBTORS']),
                AccountGroup.is_active == True
            ).first()
            
            if receivable_group:
                parent_group_id = receivable_group.id
            else:
                # Try to find any ASSET group
                asset_group = session.query(AccountGroup).filter(
                    AccountGroup.tenant_id == tenant_id,
                    AccountGroup.account_type == 'ASSET',
                    AccountGroup.is_active == True
                ).first()
                
                if asset_group:
                    parent_group_id = asset_group.id
        
        # If still no group found, raise error
        if not parent_group_id:
            raise ValueError("No suitable account group found for customer accounts. Please configure Accounts Receivable group or ASSET account groups.")
        
        # Generate unique code for customer account
        customer_code = f"AR-{customer_id:06d}"
        
        # Check if code already exists and make it unique
        existing = session.query(AccountMaster).filter(
            AccountMaster.tenant_id == tenant_id,
            AccountMaster.code == customer_code,
            AccountMaster.is_deleted == False
        ).first()
        
        if existing:
            # Add timestamp suffix to make it unique
            import time
            customer_code = f"AR-{customer_id:06d}-{int(time.time())}"
        
        # Create new customer account
        customer_account = AccountMaster(
            tenant_id=tenant_id,
            parent_id=parent_account_id,
            account_group_id=parent_group_id,
            code=customer_code,
            name=f"{customer.name} - Receivable",
            description=f"Account receivable for customer {customer.name}",
            account_type='ASSET',
            normal_balance='D',
            system_code=f'CUSTOMER_{customer_id}',
            is_system_account=False,
            level=2 if parent_account_id else 1,
            opening_balance=Decimal(0),
            current_balance=Decimal(0),
            is_active=True,
            is_deleted=False,
            created_by=username,
            updated_by=username
        )
        
        session.add(customer_account)
        session.flush()
        
        return customer_account.id
    
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
            cgst_output_id = self._get_configured_account(session, tenant_id, 'GST_OUTPUT_CGST')
            sgst_output_id = self._get_configured_account(session, tenant_id, 'GST_OUTPUT_SGST')
            igst_output_id = self._get_configured_account(session, tenant_id, 'GST_OUTPUT_IGST')
        except ValueError as e:
            raise ValueError(f"Account configuration error: {str(e)}. Please run tenant accounting initialization.")
        
        # Get or create customer-specific account
        customer_account_id = self._get_or_create_customer_account(session, tenant_id, invoice.customer_id, username)
        
        # Create voucher lines
        line_no = 1
        
        # Debit: Customer-Specific Account Receivable
        from modules.inventory_module.models.customer_entity import Customer
        customer = session.query(Customer).filter(Customer.id == invoice.customer_id).first()
        customer_name = customer.name if customer else f"Customer {invoice.customer_id}"
        
        customer_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=line_no,
            account_id=customer_account_id,
            description=f"{customer_name} - Invoice {invoice.invoice_number}",
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
        
        # CESS if applicable
        if invoice.cess_amount_base > 0:
            try:
                cess_output_id = self._get_configured_account(session, tenant_id, 'GST_OUTPUT_CESS')
                cess_line = VoucherLine(
                    tenant_id=tenant_id,
                    voucher_id=voucher.id,
                    line_no=line_no,
                    account_id=cess_output_id,
                    description="CESS Output",
                    debit_base=Decimal(0),
                    credit_base=invoice.cess_amount_base,
                    tax_amount_base=invoice.cess_amount_base,
                    reference_type='SALES_INVOICE',
                    reference_id=invoice.id,
                    created_by=username,
                    updated_by=username
                )
                session.add(cess_line)
                line_no += 1
            except ValueError:
                pass  # CESS account not configured
        
        return voucher
    
    def _create_payment(self, session, tenant_id, username, invoice, payment_number, payment_details_data, payment_remarks):
        """Create payment record and voucher for the sales invoice"""
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
            remarks=payment_remarks or f"Receipt for invoice {invoice.invoice_number}",
            created_by=username,
            updated_by=username
        )
        
        session.add(payment)
        session.flush()
        
        # Create payment details
        for detail_data in payment_details_data:
            # Get account_id - auto-determine if not provided
            account_id = detail_data.get('account_id')
            if not account_id:
                # Use default cash/bank account based on payment mode
                payment_mode = detail_data.get('payment_mode', 'CASH')
                try:
                    if payment_mode == 'CASH':
                        account_id = self._get_configured_account(session, tenant_id, 'CASH')
                    else:
                        account_id = self._get_configured_account(session, tenant_id, 'BANK')
                except ValueError:
                    # If no configured account, try to create or find a fallback account
                    account_id = self._get_or_create_cash_bank_account(session, tenant_id, payment_mode, username)
                    if not account_id:
                        raise ValueError(f"Unable to determine account for payment mode {payment_mode}. Please configure CASH/BANK accounts.")
            
            # Ensure account_id is determined before creating the record
            if not account_id:
                raise ValueError(f"Account ID could not be determined for payment detail with mode {detail_data.get('payment_mode', 'UNKNOWN')}")
            
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
                account_id=account_id,
                description=detail_data.get('description'),
                created_by=username,
                updated_by=username
            )
            session.add(detail)
        
        # Create payment voucher
        self._create_payment_voucher(session, tenant_id, username, invoice, payment, payment_details_data)
        
        return payment
    
    def _create_payment_voucher(self, session, tenant_id, username, invoice, payment, payment_details_data):
        """Create accounting voucher for payment receipt"""
        # Get or create Receipt voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.tenant_id == tenant_id,
            VoucherType.code == 'RECEIPT',
            VoucherType.is_active == True,
            VoucherType.is_deleted == False
        ).first()
        
        if not voucher_type:
            raise ValueError("Receipt voucher type not configured. Please configure 'RECEIPT' voucher type.")
        
        # Generate voucher number
        voucher_number = f"REC-{payment.payment_number}"
        
        # Create voucher
        voucher = Voucher(
            tenant_id=tenant_id,
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=payment.payment_date if hasattr(payment.payment_date, 'hour') else datetime.combine(payment.payment_date, datetime.min.time()),
            base_currency_id=payment.base_currency_id,
            foreign_currency_id=payment.foreign_currency_id,
            exchange_rate=payment.exchange_rate,
            base_total_amount=payment.total_amount_base,
            base_total_debit=payment.total_amount_base,
            base_total_credit=payment.total_amount_base,
            foreign_total_amount=payment.total_amount_foreign,
            foreign_total_debit=payment.total_amount_foreign,
            foreign_total_credit=payment.total_amount_foreign,
            reference_type='PAYMENT',
            reference_id=payment.id,
            reference_number=payment.payment_number,
            narration=f"Receipt {payment.payment_number} for invoice {invoice.invoice_number}",
            is_posted=True,
            created_by=username,
            updated_by=username
        )
        
        session.add(voucher)
        session.flush()
        
        # Update payment with voucher reference
        payment.voucher_id = voucher.id
        
        # Get customer account
        customer_account_id = self._get_or_create_customer_account(session, tenant_id, invoice.customer_id, username)
        
        # Create voucher lines
        line_no = 1
        
        # Debit: Bank/Cash Accounts (based on payment details)
        for detail_data in payment_details_data:
            payment_mode = detail_data.get('payment_mode', 'CASH')
            amount = Decimal(str(detail_data.get('amount_base', 0)))
            
            # Get payment account from detail or use configured default  
            payment_account_id = detail_data.get('account_id')
            if not payment_account_id and detail_data.get('bank_account_id'):
                payment_account_id = detail_data.get('bank_account_id')
            
            if not payment_account_id:
                # Use default cash/bank account based on mode
                try:
                    if payment_mode == 'CASH':
                        payment_account_id = self._get_configured_account(session, tenant_id, 'CASH')
                    else:
                        payment_account_id = self._get_configured_account(session, tenant_id, 'BANK')
                except ValueError:
                    # If no configured account, try to create or find a fallback account
                    payment_account_id = self._get_or_create_cash_bank_account(session, tenant_id, payment_mode, username)
                    if not payment_account_id:
                        raise ValueError(f"Payment account not configured for mode {payment_mode}. Please configure CASH/BANK accounts.")
            
            payment_description = detail_data.get('description') or f"{payment_mode} receipt"
            if detail_data.get('instrument_number'):
                payment_description += f" - {detail_data.get('instrument_number')}"
            
            payment_line = VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=payment_account_id,
                description=payment_description,
                debit_base=amount,
                credit_base=Decimal(0),
                debit_foreign=detail_data.get('amount_foreign'),
                credit_foreign=Decimal(0) if detail_data.get('amount_foreign') else None,
                reference_type='PAYMENT',
                reference_id=payment.id,
                created_by=username,
                updated_by=username
            )
            session.add(payment_line)
            line_no += 1
        
        # Credit: Customer Account (reduces asset/receivable)
        from modules.inventory_module.models.customer_entity import Customer
        customer = session.query(Customer).filter(Customer.id == invoice.customer_id).first()
        customer_name = customer.name if customer else f"Customer {invoice.customer_id}"
        
        customer_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=line_no,
            account_id=customer_account_id,
            description=f"{customer_name} - Receipt for Invoice {invoice.invoice_number}",
            debit_base=Decimal(0),
            credit_base=payment.total_amount_base,
            debit_foreign=Decimal(0) if payment.total_amount_foreign else None,
            credit_foreign=payment.total_amount_foreign,
            reference_type='PAYMENT',
            reference_id=payment.id,
            created_by=username,
            updated_by=username
        )
        session.add(customer_line)
        
        return voucher
    
    @ExceptionMiddleware.handle_exceptions("SalesInvoiceService")
    def get_all(self, page=1, page_size=100, search=None, status=None, customer_id=None, 
                date_from=None, date_to=None, invoice_type=None):
        """Get all sales invoices with pagination and filters, including customer and payment info"""
        from modules.inventory_module.models.customer_entity import Customer
        
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
            
            # Convert invoices to dict and add customer and payment info
            invoice_data = []
            for inv in invoices:
                inv_dict = self._to_dict(inv, include_items=False)
                
                # Add customer information
                if inv.customer_id:
                    customer = session.query(Customer).filter(
                        Customer.id == inv.customer_id
                    ).first()
                    
                    if customer:
                        inv_dict['customer_name'] = customer.name
                        inv_dict['customer_phone'] = customer.phone
                    else:
                        inv_dict['customer_name'] = None
                        inv_dict['customer_phone'] = None
                else:
                    inv_dict['customer_name'] = None
                    inv_dict['customer_phone'] = None
                
                # Add payment information (multiple payments possible)
                payments = session.query(Payment).filter(
                    Payment.party_type == 'CUSTOMER',
                    Payment.party_id == inv.customer_id,
                    Payment.reference_number == inv.invoice_number,
                    Payment.tenant_id == tenant_id,
                    Payment.is_deleted == False
                ).all()
                
                inv_dict['payments'] = []
                if payments:
                    for payment in payments:
                        inv_dict['payments'].append({
                            'payment_id': payment.id,
                            'payment_number': payment.payment_number,
                            'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                            'payment_amount': float(payment.total_amount_base) if payment.total_amount_base else 0.0,
                            'payment_status': payment.status
                        })
                
                invoice_data.append(inv_dict)
            
            return {
                'total': total,
                'page': page,
                'per_page': page_size,
                'total_pages': math.ceil(total / page_size) if total > 0 else 0,
                'data': invoice_data
            }
    
    @ExceptionMiddleware.handle_exceptions("SalesInvoiceService")
    def get_by_id(self, invoice_id: int):
        """Get a specific sales invoice by ID with items, customer info, product names, and payment info"""
        from modules.inventory_module.models.customer_entity import Customer
        from modules.inventory_module.models.product_entity import Product
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            invoice = session.query(SalesInvoice).filter(
                SalesInvoice.id == invoice_id,
                SalesInvoice.tenant_id == tenant_id,
                SalesInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                raise ValueError(f"Sales invoice with ID {invoice_id} not found")
            
            result = self._to_dict(invoice, include_items=True)
            
            # Add customer information
            if invoice.customer_id:
                customer = session.query(Customer).filter(
                    Customer.id == invoice.customer_id,
                    Customer.tenant_id == tenant_id
                ).first()
                
                if customer:
                    result['customer'] = {
                        'id': customer.id,
                        'name': customer.name,
                        'phone': customer.phone,
                        'email': customer.email,
                        'address': customer.address,
                        'tax_id': customer.tax_id
                    }
            
            # Add product names to items
            if 'items' in result:
                for item in result['items']:
                    if item.get('product_id'):
                        product = session.query(Product).filter(
                            Product.id == item['product_id'],
                            Product.tenant_id == tenant_id
                        ).first()
                        
                        if product:
                            item['product_name'] = product.name
                            item['product_code'] = product.code
            
            # Add payment information (multiple payments possible)
            payments = session.query(Payment).filter(
                Payment.party_type == 'CUSTOMER',
                Payment.party_id == invoice.customer_id,
                Payment.reference_number == invoice.invoice_number,
                Payment.tenant_id == tenant_id,
                Payment.is_deleted == False
            ).all()
            
            result['payments'] = []
            if payments:
                for payment in payments:
                    payment_obj = {
                        'id': payment.id,
                        'payment_number': payment.payment_number,
                        'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                        'payment_type': payment.payment_type,
                        'total_amount_base': float(payment.total_amount_base) if payment.total_amount_base else 0.0,
                        'total_amount_foreign': float(payment.total_amount_foreign) if payment.total_amount_foreign else None,
                        'voucher_id': payment.voucher_id,
                        'remarks': payment.remarks,
                        'details': []
                    }
                    
                    # Add payment details
                    payment_details = session.query(PaymentDetail).filter(
                        PaymentDetail.payment_id == payment.id,
                        PaymentDetail.tenant_id == tenant_id
                    ).all()
                    
                    if payment_details:
                        payment_obj['details'] = [
                            {
                                'id': detail.id,
                                'line_no': detail.line_no,
                                'payment_mode': detail.payment_mode,
                                'amount_base': float(detail.amount_base) if detail.amount_base else 0.0,
                                'amount_foreign': float(detail.amount_foreign) if detail.amount_foreign else None,
                                'bank_account_id': detail.bank_account_id,
                                'instrument_number': detail.instrument_number,
                                'instrument_date': detail.instrument_date.isoformat() if detail.instrument_date else None,
                                'bank_name': detail.bank_name,
                                'branch_name': detail.branch_name,
                                'ifsc_code': detail.ifsc_code,
                                'transaction_reference': detail.transaction_reference,
                                'description': detail.description
                            }
                            for detail in payment_details
                        ]
                    
                    result['payments'].append(payment_obj)
            
            return result
    
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
                    # Reverse existing stock transactions
                    stock_service = StockService()
                    stock_service.reverse_sales_invoice_transaction_in_session(
                        session=session,
                        tenant_id=tenant_id,
                        invoice_id=invoice_id,
                        username=username
                    )
                    
                    # Delete existing items
                    session.query(SalesInvoiceItem).filter(
                        SalesInvoiceItem.invoice_id == invoice_id
                    ).delete()
                    
                    # Create new items
                    for item_data in items_data:
                        # Ensure free_quantity has default value
                        if 'free_quantity' not in item_data:
                            item_data['free_quantity'] = 0
                        item = SalesInvoiceItem(
                            tenant_id=tenant_id,
                            invoice_id=invoice.id,
                            **item_data,
                            created_by=username,
                            updated_by=username
                        )
                        session.add(item)
                    
                    # Flush to get new item IDs
                    session.flush()
                    
                    # Record new stock transactions
                    stock_service.record_sales_invoice_transaction_in_session(
                        session=session,
                        tenant_id=tenant_id,
                        invoice_id=invoice.id,
                        invoice_number=invoice.invoice_number,
                        invoice_date=invoice.invoice_date,
                        items_data=items_data,
                        username=username
                    )
                
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
                
                # Reverse stock transactions
                stock_service = StockService()
                stock_service.reverse_sales_invoice_transaction_in_session(
                    session=session,
                    tenant_id=tenant_id,
                    invoice_id=invoice_id,
                    username=username
                )
                
                invoice.is_deleted = True
                invoice.updated_by = username
                invoice.updated_at = datetime.utcnow()
                
                session.commit()
                
                return {"message": "Sales invoice deleted successfully"}
                
            except Exception as e:
                session.rollback()
                raise
    
    @ExceptionMiddleware.handle_exceptions("SalesInvoiceService")
    def update_payment(self, invoice_id: int, payment_amount: Decimal):
        """Update payment information for an invoice"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            invoice = session.query(SalesInvoice).filter(
                SalesInvoice.id == invoice_id,
                SalesInvoice.tenant_id == tenant_id,
                SalesInvoice.is_deleted == False
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
                    'free_quantity': float(item.free_quantity) if item.free_quantity else 0.0,
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
