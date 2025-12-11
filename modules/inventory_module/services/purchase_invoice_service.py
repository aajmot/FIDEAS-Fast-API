from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from modules.inventory_module.models.purchase_invoice_entity import PurchaseInvoice, PurchaseInvoiceItem
from modules.account_module.models.entities import Voucher, VoucherLine, VoucherType
from modules.account_module.models.account_configuration_entity import AccountConfiguration
from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey
from modules.account_module.models.payment_entity import Payment, PaymentDetail
from modules.inventory_module.services.stock_service import StockService
from modules.account_module.services.voucher_service import VoucherService
from modules.account_module.services.payment_service import PaymentService
from sqlalchemy import func, or_
from decimal import Decimal
from datetime import datetime
import math


class PurchaseInvoiceService:
    """Service layer for purchase invoice management"""
    
    def __init__(self):
        self.voucher_service = VoucherService()
        self.payment_service = PaymentService()
    
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
                paid_amount = Decimal('0.0000')
                if payment_details_data:
                    paid_amount = sum(Decimal(str(detail.get('amount_base', 0))) for detail in payment_details_data)
                
                # Update invoice paid_amount and balance_amount
                total_amount = Decimal(str(invoice_data.get('total_amount_base', 0)))
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
                
                # Set exchange rate to 1 if not provided and ensure it's Decimal
                exchange_rate = invoice_data.get('exchange_rate')
                if exchange_rate is None or exchange_rate == '':
                    exchange_rate = Decimal('1.0000')
                else:
                    exchange_rate = Decimal(str(exchange_rate))
                invoice_data['exchange_rate'] = exchange_rate
                
                # Convert and round all amounts to proper Decimal with 2 decimal places for consistency
                cgst_amount = Decimal(str(invoice_data.get('cgst_amount_base', 0))).quantize(Decimal('0.01'))
                sgst_amount = Decimal(str(invoice_data.get('sgst_amount_base', 0))).quantize(Decimal('0.01'))
                igst_amount = Decimal(str(invoice_data.get('igst_amount_base', 0))).quantize(Decimal('0.01'))
                ugst_amount = Decimal(str(invoice_data.get('ugst_amount_base', 0))).quantize(Decimal('0.01'))
                cess_amount = Decimal(str(invoice_data.get('cess_amount_base', 0))).quantize(Decimal('0.01'))
                
                # Recalculate tax_amount to match sum of GST components (fixes rounding issues)
                tax_amount = (cgst_amount + sgst_amount + igst_amount + ugst_amount + cess_amount).quantize(Decimal('0.01'))
                
                subtotal = Decimal(str(invoice_data.get('subtotal_base', 0))).quantize(Decimal('0.01'))
                discount_amount = Decimal(str(invoice_data.get('discount_amount_base', 0))).quantize(Decimal('0.01'))
                
                # Recalculate total_amount = subtotal + tax_amount (subtotal should already have discount applied)
                total_amount = (subtotal + tax_amount).quantize(Decimal('0.01'))
                
                # Update invoice_data with corrected total_amount
                invoice_data['total_amount_base'] = total_amount
                
                # Update paid and balance based on the corrected total
                paid_amount = invoice_data['paid_amount_base']
                balance_amount = (total_amount - paid_amount).quantize(Decimal('0.01'))
                
                # Ensure balance doesn't go negative due to rounding (if paid >= total, set to 0)
                if balance_amount < 0 and abs(balance_amount) < Decimal('0.01'):
                    balance_amount = Decimal('0.00')
                
                # Update invoice_data with corrected amounts
                invoice_data['balance_amount_base'] = balance_amount
                
                # Update status based on corrected amounts - ensure proper alignment
                if balance_amount <= 0:
                    invoice_data['status'] = 'PAID'
                elif paid_amount > 0:
                    invoice_data['status'] = 'PARTIALLY_PAID'
                else:
                    invoice_data['status'] = 'POSTED'
                
                # Create invoice header with corrected amounts
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
                    exchange_rate=invoice_data['exchange_rate'],
                    cgst_amount_base=cgst_amount,
                    sgst_amount_base=sgst_amount,
                    igst_amount_base=igst_amount,
                    ugst_amount_base=ugst_amount,
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
                    notes=invoice_data.get('notes'),
                    tags=invoice_data.get('tags'),
                    created_by=username,
                    updated_by=username
                )
                
                session.add(invoice)
                session.flush()  # Get invoice ID
                
                # Create invoice items
                invoice_items = []
                for item_data in items_data:
                    # Calculate and validate GST components
                    cgst_amount = Decimal(str(item_data.get('cgst_amount_base', 0))).quantize(Decimal('0.01'))
                    sgst_amount = Decimal(str(item_data.get('sgst_amount_base', 0))).quantize(Decimal('0.01'))
                    igst_amount = Decimal(str(item_data.get('igst_amount_base', 0))).quantize(Decimal('0.01'))
                    ugst_amount = Decimal(str(item_data.get('ugst_amount_base', 0))).quantize(Decimal('0.01'))
                    cess_amount = Decimal(str(item_data.get('cess_amount_base', 0))).quantize(Decimal('0.01'))
                    
                    # Recalculate tax_amount to ensure constraint compliance
                    tax_amount = (cgst_amount + sgst_amount + igst_amount + ugst_amount + cess_amount).quantize(Decimal('0.01'))
                    
                    # Recalculate total_amount
                    taxable_amount = Decimal(str(item_data.get('taxable_amount_base', 0))).quantize(Decimal('0.01'))
                    total_amount = (taxable_amount + tax_amount).quantize(Decimal('0.01'))
                    
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
                        free_quantity=item_data.get('free_quantity', 0),
                        uom=item_data.get('uom', 'NOS'),
                        unit_price_base=item_data.get('unit_price_base'),
                        discount_percent=item_data.get('discount_percent', 0),
                        discount_amount_base=item_data.get('discount_amount_base', 0),
                        taxable_amount_base=taxable_amount,
                        cgst_rate=item_data.get('cgst_rate', 0),
                        cgst_amount_base=cgst_amount,
                        sgst_rate=item_data.get('sgst_rate', 0),
                        sgst_amount_base=sgst_amount,
                        igst_rate=item_data.get('igst_rate', 0),
                        igst_amount_base=igst_amount,
                        ugst_rate=item_data.get('ugst_rate', 0),
                        ugst_amount_base=ugst_amount,
                        cess_rate=item_data.get('cess_rate', 0),
                        cess_amount_base=cess_amount,
                        tax_amount_base=tax_amount,
                        total_amount_base=total_amount,
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
                    invoice_items.append(item)
                
                # Flush to get item IDs
                session.flush()
                
                # Record stock transactions for purchase invoice items
                stock_service = StockService()
                stock_service.record_purchase_invoice_transaction_in_session(
                    session=session,
                    invoice=invoice,
                    items=invoice_items
                )
                
                # Create accounting voucher for the purchase invoice
                voucher = self._create_purchase_voucher_in_session(
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
                        payment_number = f"PAY-{invoice.invoice_number}"
                    
                    payment = self._create_payment_in_session(
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
    
    def _get_or_create_vendor_account(self, session, tenant_id, supplier_id, username):
        """Get or create account master for vendor/supplier"""
        from modules.inventory_module.models.supplier_entity import Supplier
        from modules.account_module.models.entities import AccountMaster, AccountGroup
        
        # Get supplier details
        supplier = session.query(Supplier).filter(
            Supplier.id == supplier_id,
            Supplier.tenant_id == tenant_id,
            Supplier.is_deleted == False
        ).first()
        
        if not supplier:
            raise ValueError(f"Supplier with ID {supplier_id} not found")
        
        # Check if vendor account already exists
        vendor_account = session.query(AccountMaster).filter(
            AccountMaster.tenant_id == tenant_id,
            AccountMaster.system_code == f'VENDOR_{supplier_id}',
            AccountMaster.is_deleted == False
        ).first()
        
        if vendor_account:
            return vendor_account.id
        
        # Try to get Accounts Payable account as parent
        # First try to get from configured account
        parent_account_id = None
        parent_group_id = None
        
        try:
            # Try to get configured Accounts Payable account
            payable_account_id = self._get_configured_account(session, tenant_id, 'ACCOUNTS_PAYABLE')
            payable_account = session.query(AccountMaster).filter(
                AccountMaster.id == payable_account_id,
                AccountMaster.tenant_id == tenant_id
            ).first()
            
            if payable_account:
                parent_account_id = payable_account.id
                parent_group_id = payable_account.account_group_id
        except ValueError:
            # If no configured account, try to find Accounts Payable group
            payable_group = session.query(AccountGroup).filter(
                AccountGroup.tenant_id == tenant_id,
                AccountGroup.code.in_(['ACCOUNTS_PAYABLE', 'SUNDRY_CREDITORS', 'CREDITORS']),
                AccountGroup.is_active == True
            ).first()
            
            if payable_group:
                parent_group_id = payable_group.id
            else:
                # Try to find any LIABILITY group
                liability_group = session.query(AccountGroup).filter(
                    AccountGroup.tenant_id == tenant_id,
                    AccountGroup.account_type == 'LIABILITY',
                    AccountGroup.is_active == True
                ).first()
                
                if liability_group:
                    parent_group_id = liability_group.id
        
        # If still no group found, raise error
        if not parent_group_id:
            raise ValueError("No suitable account group found for vendor accounts. Please configure Accounts Payable group or LIABILITY account groups.")
        
        # Generate unique code for vendor account
        vendor_code = f"AP-{supplier_id:06d}"
        
        # Check if code already exists and make it unique
        existing = session.query(AccountMaster).filter(
            AccountMaster.tenant_id == tenant_id,
            AccountMaster.code == vendor_code,
            AccountMaster.is_deleted == False
        ).first()
        
        if existing:
            # Add timestamp suffix to make it unique
            import time
            vendor_code = f"AP-{supplier_id:06d}-{int(time.time())}"
        
        # Create new vendor account
        vendor_account = AccountMaster(
            tenant_id=tenant_id,
            parent_id=parent_account_id,
            account_group_id=parent_group_id,
            code=vendor_code,
            name=f"{supplier.name} - Payable",
            description=f"Account payable for supplier {supplier.name}",
            account_type='LIABILITY',
            normal_balance='C',
            system_code=f'VENDOR_{supplier_id}',
            is_system_account=False,
            level=2 if parent_account_id else 1,
            opening_balance=Decimal(0),
            current_balance=Decimal(0),
            is_active=True,
            is_deleted=False,
            created_by=username,
            updated_by=username
        )
        
        session.add(vendor_account)
        session.flush()
        
        return vendor_account.id
    
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
    
    def _create_purchase_voucher_in_session(self, session, tenant_id, username, invoice, items_data):
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
            cgst_input_id = self._get_configured_account(session, tenant_id, 'GST_INPUT_CGST')
            sgst_input_id = self._get_configured_account(session, tenant_id, 'GST_INPUT_SGST')
            igst_input_id = self._get_configured_account(session, tenant_id, 'GST_INPUT_IGST')
        except ValueError as e:
            raise ValueError(f"Account configuration error: {str(e)}. Please run tenant accounting initialization.")
        
        # Get or create vendor-specific account
        vendor_account_id = self._get_or_create_vendor_account(session, tenant_id, invoice.supplier_id, username)
        
        # Create voucher lines
        line_no = 1
        
        # Debit: Purchase Expense Account
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
        
        # Debit: Tax Accounts (CGST, SGST, IGST)
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
        
        # UGST and CESS if applicable
        if invoice.ugst_amount_base > 0:
            try:
                ugst_input_id = self._get_configured_account(session, tenant_id, 'GST_INPUT_UGST')
                ugst_line = VoucherLine(
                    tenant_id=tenant_id,
                    voucher_id=voucher.id,
                    line_no=line_no,
                    account_id=ugst_input_id,
                    description="UGST Input",
                    debit_base=invoice.ugst_amount_base,
                    credit_base=Decimal(0),
                    tax_amount_base=invoice.ugst_amount_base,
                    reference_type='PURCHASE_INVOICE',
                    reference_id=invoice.id,
                    created_by=username,
                    updated_by=username
                )
                session.add(ugst_line)
                line_no += 1
            except ValueError:
                pass  # UGST account not configured
        
        if invoice.cess_amount_base > 0:
            try:
                cess_input_id = self._get_configured_account(session, tenant_id, 'GST_INPUT_CESS')
                cess_line = VoucherLine(
                    tenant_id=tenant_id,
                    voucher_id=voucher.id,
                    line_no=line_no,
                    account_id=cess_input_id,
                    description="CESS Input",
                    debit_base=invoice.cess_amount_base,
                    credit_base=Decimal(0),
                    tax_amount_base=invoice.cess_amount_base,
                    reference_type='PURCHASE_INVOICE',
                    reference_id=invoice.id,
                    created_by=username,
                    updated_by=username
                )
                session.add(cess_line)
                line_no += 1
            except ValueError:
                pass  # CESS account not configured
        
        # Credit: Vendor-Specific Account Payable
        from modules.inventory_module.models.supplier_entity import Supplier
        supplier = session.query(Supplier).filter(Supplier.id == invoice.supplier_id).first()
        supplier_name = supplier.name if supplier else f"Supplier {invoice.supplier_id}"
        
        supplier_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=line_no,
            account_id=vendor_account_id,
            description=f"{supplier_name} - Invoice {invoice.invoice_number}",
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
    
    def _create_payment_in_session(self, session, tenant_id, username, invoice, payment_number, payment_details_data, payment_remarks):
        """Create payment record and voucher for the purchase invoice"""
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
            # Get account_id - required field
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
                        continue
            
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
        self._create_payment_voucher_in_session(session, tenant_id, username, invoice, payment, payment_details_data)
        
        return payment
    
    def _create_payment_voucher_in_session(self, session, tenant_id, username, invoice, payment, payment_details_data):
        """Create accounting voucher for payment"""
        # Get or create Payment voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.tenant_id == tenant_id,
            VoucherType.code == 'PAYMENT',
            VoucherType.is_active == True,
            VoucherType.is_deleted == False
        ).first()
        
        if not voucher_type:
            raise ValueError("Payment voucher type not configured. Please configure 'PAYMENT' voucher type.")
        
        # Generate voucher number
        voucher_number = f"PAY-{payment.payment_number}"
        
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
            narration=f"Payment {payment.payment_number} for invoice {invoice.invoice_number}",
            is_posted=True,
            created_by=username,
            updated_by=username
        )
        
        session.add(voucher)
        session.flush()
        
        # Update payment with voucher reference
        payment.voucher_id = voucher.id
        
        # Get vendor account
        vendor_account_id = self._get_or_create_vendor_account(session, tenant_id, invoice.supplier_id, username)
        
        # Create voucher lines
        line_no = 1
        
        # Debit: Vendor Account (reduces liability)
        from modules.inventory_module.models.supplier_entity import Supplier
        supplier = session.query(Supplier).filter(Supplier.id == invoice.supplier_id).first()
        supplier_name = supplier.name if supplier else f"Supplier {invoice.supplier_id}"
        
        vendor_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=line_no,
            account_id=vendor_account_id,
            description=f"{supplier_name} - Payment for Invoice {invoice.invoice_number}",
            debit_base=payment.total_amount_base,
            credit_base=Decimal(0),
            debit_foreign=payment.total_amount_foreign,
            credit_foreign=Decimal(0) if payment.total_amount_foreign else None,
            reference_type='PAYMENT',
            reference_id=payment.id,
            created_by=username,
            updated_by=username
        )
        session.add(vendor_line)
        line_no += 1
        
        # Credit: Bank/Cash Accounts (based on payment details)
        for detail_data in payment_details_data:
            payment_mode = detail_data.get('payment_mode', 'CASH')
            amount = Decimal(str(detail_data.get('amount_base', 0)))
            
            # Get payment account from detail or use configured default
            if detail_data.get('account_id'):
                payment_account_id = detail_data.get('account_id')
            elif detail_data.get('bank_account_id'):
                payment_account_id = detail_data.get('bank_account_id')
            else:
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
            
            payment_description = detail_data.get('description') or f"{payment_mode} payment"
            if detail_data.get('instrument_number'):
                payment_description += f" - {detail_data.get('instrument_number')}"
            
            payment_line = VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=payment_account_id,
                description=payment_description,
                debit_base=Decimal(0),
                credit_base=amount,
                debit_foreign=Decimal(0) if detail_data.get('amount_foreign') else None,
                credit_foreign=detail_data.get('amount_foreign'),
                reference_type='PAYMENT',
                reference_id=payment.id,
                created_by=username,
                updated_by=username
            )
            session.add(payment_line)
            line_no += 1
        
        return voucher
    
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
                # Get existing items for stock reversal
                existing_items = session.query(PurchaseInvoiceItem).filter(
                    PurchaseInvoiceItem.invoice_id == invoice_id
                ).all()
                
                # Reverse stock transactions for existing items
                if existing_items:
                    stock_service = StockService()
                    stock_service.reverse_purchase_invoice_transaction_in_session(
                        session=session,
                        invoice=invoice,
                        items=existing_items
                    )
                
                # Delete existing items
                session.query(PurchaseInvoiceItem).filter(
                    PurchaseInvoiceItem.invoice_id == invoice_id
                ).delete()
                
                # Add new items
                new_items = []
                for item_data in items_data:
                    # Calculate and validate GST components
                    cgst_amount = Decimal(str(item_data.get('cgst_amount_base', 0))).quantize(Decimal('0.01'))
                    sgst_amount = Decimal(str(item_data.get('sgst_amount_base', 0))).quantize(Decimal('0.01'))
                    igst_amount = Decimal(str(item_data.get('igst_amount_base', 0))).quantize(Decimal('0.01'))
                    ugst_amount = Decimal(str(item_data.get('ugst_amount_base', 0))).quantize(Decimal('0.01'))
                    cess_amount = Decimal(str(item_data.get('cess_amount_base', 0))).quantize(Decimal('0.01'))
                    
                    # Recalculate tax_amount to ensure constraint compliance
                    tax_amount = (cgst_amount + sgst_amount + igst_amount + ugst_amount + cess_amount).quantize(Decimal('0.01'))
                    
                    # Recalculate total_amount
                    taxable_amount = Decimal(str(item_data.get('taxable_amount_base', 0))).quantize(Decimal('0.01'))
                    total_amount = (taxable_amount + tax_amount).quantize(Decimal('0.01'))
                    
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
                        free_quantity=item_data.get('free_quantity', 0),
                        uom=item_data.get('uom', 'NOS'),
                        unit_price_base=item_data.get('unit_price_base'),
                        discount_percent=item_data.get('discount_percent', 0),
                        discount_amount_base=item_data.get('discount_amount_base', 0),
                        taxable_amount_base=taxable_amount,
                        cgst_rate=item_data.get('cgst_rate', 0),
                        cgst_amount_base=cgst_amount,
                        sgst_rate=item_data.get('sgst_rate', 0),
                        sgst_amount_base=sgst_amount,
                        igst_rate=item_data.get('igst_rate', 0),
                        igst_amount_base=igst_amount,
                        ugst_rate=item_data.get('ugst_rate', 0),
                        ugst_amount_base=ugst_amount,
                        cess_rate=item_data.get('cess_rate', 0),
                        cess_amount_base=cess_amount,
                        tax_amount_base=tax_amount,
                        total_amount_base=total_amount,
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
                    new_items.append(item)
                
                # Flush to get new item IDs
                session.flush()
                
                # Record stock transactions for new items
                if new_items:
                    stock_service = StockService()
                    stock_service.record_purchase_invoice_transaction_in_session(
                        session=session,
                        invoice=invoice,
                        items=new_items
                    )
            
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
            
            # Reverse stock transactions for the invoice items
            items = session.query(PurchaseInvoiceItem).filter(
                PurchaseInvoiceItem.invoice_id == invoice_id
            ).all()
            
            if items:
                stock_service = StockService()
                stock_service.reverse_purchase_invoice_transaction_in_session(
                    session=session,
                    invoice=invoice,
                    items=items
                )
            
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
            'free_quantity': item.free_quantity,
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
    
    def create_purchase_voucher(self, invoice_id: int, items_data: list = None):
        """Create purchase voucher using voucher service"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            invoice = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                raise ValueError(f"Purchase invoice with ID {invoice_id} not found")
            
            if invoice.voucher_id:
                raise ValueError("Voucher already exists for this invoice")
            
            # Get items if not provided
            if not items_data:
                items = session.query(PurchaseInvoiceItem).filter(
                    PurchaseInvoiceItem.invoice_id == invoice_id
                ).all()
                items_data = [self._item_to_dict(item) for item in items]
            
            # Create voucher
            voucher = self._create_purchase_voucher_in_session(
                session=session,
                tenant_id=tenant_id,
                username=username,
                invoice=invoice,
                items_data=items_data
            )
            
            # Link voucher to invoice
            invoice.voucher_id = voucher.id
            
            session.commit()
            return voucher.id
    
    def create_purchase_payment(self, invoice_id: int, payment_data: dict):
        """Create payment for purchase invoice using payment service"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            invoice = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                raise ValueError(f"Purchase invoice with ID {invoice_id} not found")
            
            # Extract payment details
            payment_details_data = payment_data.get('payment_details', [])
            payment_number = payment_data.get('payment_number')
            payment_remarks = payment_data.get('payment_remarks')
            
            if not payment_number:
                payment_number = f"PAY-{invoice.invoice_number}"
            
            # Create payment
            payment = self._create_payment_in_session(
                session=session,
                tenant_id=tenant_id,
                username=username,
                invoice=invoice,
                payment_number=payment_number,
                payment_details_data=payment_details_data,
                payment_remarks=payment_remarks
            )
            
            # Update invoice payment status
            paid_amount = sum(Decimal(str(detail.get('amount_base', 0))) for detail in payment_details_data)
            invoice.paid_amount_base = (invoice.paid_amount_base or Decimal('0')) + paid_amount
            invoice.balance_amount_base = invoice.total_amount_base - invoice.paid_amount_base
            
            # Update status
            if invoice.balance_amount_base <= 0:
                invoice.status = 'PAID'
            elif invoice.paid_amount_base > 0:
                invoice.status = 'PARTIALLY_PAID'
            
            invoice.updated_by = username
            
            session.commit()
            return payment.id
    
    @ExceptionMiddleware.handle_exceptions("PurchaseInvoiceService")
    def get_invoice_voucher_details(self, invoice_id: int):
        """Get voucher details for a purchase invoice"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            invoice = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
            
            if not invoice or not invoice.voucher_id:
                return None
            
            return self.voucher_service.get_by_id(invoice.voucher_id)
    
    @ExceptionMiddleware.handle_exceptions("PurchaseInvoiceService")
    def get_invoice_payments(self, invoice_id: int):
        """Get all payments for a purchase invoice"""
        from modules.account_module.models.payment_entity import Payment
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            invoice = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                return []
            
            payments = session.query(Payment).filter(
                Payment.tenant_id == tenant_id,
                Payment.party_type == 'SUPPLIER',
                Payment.party_id == invoice.supplier_id,
                Payment.reference_number == invoice.invoice_number,
                Payment.is_deleted == False
            ).all()
            
            return [self.payment_service._payment_to_dict(p, include_details=True) for p in payments]
    
    @ExceptionMiddleware.handle_exceptions("PurchaseInvoiceService")
    def validate_invoice_accounting(self, invoice_id: int):
        """Validate that invoice has proper voucher and payment entries"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            invoice = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                return {'valid': False, 'errors': ['Invoice not found']}
            
            errors = []
            
            # Check if voucher exists
            if not invoice.voucher_id:
                errors.append('Purchase voucher not created')
            else:
                voucher = session.query(Voucher).filter(
                    Voucher.id == invoice.voucher_id,
                    Voucher.tenant_id == tenant_id
                ).first()
                
                if not voucher:
                    errors.append('Purchase voucher not found')
                elif not voucher.is_posted:
                    errors.append('Purchase voucher not posted')
            
            # Check payment status alignment
            if invoice.status in ['PAID', 'PARTIALLY_PAID']:
                if invoice.paid_amount_base <= 0:
                    errors.append('Invoice marked as paid but no payment amount recorded')
                
                # Check if payment vouchers exist
                from modules.account_module.models.payment_entity import Payment
                payments = session.query(Payment).filter(
                    Payment.tenant_id == tenant_id,
                    Payment.party_type == 'SUPPLIER',
                    Payment.party_id == invoice.supplier_id,
                    Payment.reference_number == invoice.invoice_number,
                    Payment.is_deleted == False
                ).all()
                
                total_payments = sum(p.total_amount_base for p in payments)
                if abs(total_payments - invoice.paid_amount_base) > Decimal('0.01'):
                    errors.append('Payment amount mismatch between invoice and payment records')
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'invoice_id': invoice_id,
                'voucher_id': invoice.voucher_id,
                'status': invoice.status,
                'total_amount': float(invoice.total_amount_base),
                'paid_amount': float(invoice.paid_amount_base or 0),
                'balance_amount': float(invoice.balance_amount_base or 0)
            }
    
    @ExceptionMiddleware.handle_exceptions("PurchaseInvoiceService")
    def get_invoice_accounting_summary(self, invoice_id: int):
        """Get complete accounting summary for purchase invoice"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            invoice = session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
            
            if not invoice:
                return None
            
            result = {
                'invoice': self._to_dict(invoice, include_items=True),
                'voucher': None,
                'payments': [],
                'validation': self.validate_invoice_accounting(invoice_id)
            }
            
            # Get voucher details
            if invoice.voucher_id:
                result['voucher'] = self.get_invoice_voucher_details(invoice_id)
            
            # Get payment details
            result['payments'] = self.get_invoice_payments(invoice_id)
            
            return result
