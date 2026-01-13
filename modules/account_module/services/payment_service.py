from core.database.connection import db_manager
from modules.account_module.models.entities import *
from modules.account_module.services.account_service import AccountService
from modules.account_module.services.audit_service import AuditService
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from sqlalchemy import or_
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import selectinload
from modules.admin_module.models.entities import TenantSetting
import math
from modules.admin_module.services.tenant_settings_service import TenantSettingsService
from modules.inventory_module.models.customer_entity import Customer
from modules.inventory_module.models.supplier_entity import Supplier
from modules.health_module.models.clinic_entities import Patient
from modules.admin_module.services.currency_service import CurrencyService

class PaymentService:
    def __init__(self):
        self.account_service = AccountService()
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def record_sales_transaction(self, sales_order_id, sales_order_number, amount, transaction_date=None):
        """Record sales transaction (creates AR and Sales Revenue entries)"""
        with db_manager.get_session() as session:
            return self.record_sales_transaction_in_session(session, sales_order_id, sales_order_number, amount, transaction_date)
    
    def record_sales_transaction_in_session(self, session, sales_order_id, sales_order_number, amount, transaction_date=None, cogs_amount=None):
        """Record sales transaction within existing session with COGS"""
        if not transaction_date:
            transaction_date = datetime.now()
        
        tenant_id = session_manager.get_current_tenant_id()
        username = session_manager.get_current_username()
        
        # Get accounts
        ar_account = session.query(AccountMaster).filter(
            AccountMaster.code == '1100-AR',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        sales_account = session.query(AccountMaster).filter(
            AccountMaster.code == '4100-SALES',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        cogs_account = session.query(AccountMaster).filter(
            AccountMaster.code == '5100-PURCHASE',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        inventory_account = session.query(AccountMaster).filter(
            AccountMaster.code == '1200-INV',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        # Get voucher type
        voucher_type = session.query(VoucherType).filter(
                VoucherType.code == 'SAL',
            VoucherType.tenant_id == tenant_id
        ).first()
        
        if not voucher_type:
            voucher_type = session.query(VoucherType).filter(
                VoucherType.code == 'JV',
                VoucherType.tenant_id == tenant_id
            ).first()
        
        # Create voucher
        voucher_number = f"SAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        voucher = Voucher(
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=transaction_date,
            reference_type='SALES',
            reference_id=sales_order_id,
            reference_number=sales_order_number,
            narration=f'Sales transaction for Order {sales_order_number}',
            total_amount=amount,
            is_posted=True,
            tenant_id=tenant_id,
            created_by=username
        )
        session.add(voucher)
        session.flush()
        
        # Create journal
        journal = Journal(
            voucher_id=voucher.id,
            journal_date=transaction_date,
            total_debit=amount,
            total_credit=amount,
            tenant_id=tenant_id
        )
        session.add(journal)
        session.flush()
        
        # Create journal details - Debit AR, Credit Sales
        journal_details = [
            JournalDetail(
                journal_id=journal.id,
                account_id=ar_account.id,
                debit_amount=amount,
                credit_amount=0,
                narration=f'Sales on credit - SO {sales_order_number}',
                tenant_id=tenant_id
            ),
            JournalDetail(
                journal_id=journal.id,
                account_id=sales_account.id,
                debit_amount=0,
                credit_amount=amount,
                narration=f'Sales revenue - SO {sales_order_number}',
                tenant_id=tenant_id
            )
        ]
        
        for detail in journal_details:
            session.add(detail)
        
        # Create ledger entries
        ledger_entries = [
            Ledger(
                account_id=ar_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=amount,
                credit_amount=0,
                balance=ar_account.current_balance + Decimal(str(amount)),
                narration=f'Sales on credit - SO {sales_order_number}',
                tenant_id=tenant_id
            ),
            Ledger(
                account_id=sales_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=amount,
                balance=sales_account.current_balance + Decimal(str(amount)),
                narration=f'Sales revenue - SO {sales_order_number}',
                tenant_id=tenant_id
            )
        ]
        
        for ledger in ledger_entries:
            session.add(ledger)
        
        # Update account balances within same session
        self.account_service.update_account_balance_in_session(session, ar_account.id, amount, 'DEBIT')
        self.account_service.update_account_balance_in_session(session, sales_account.id, amount, 'CREDIT')
        
        # Record COGS if provided
        if cogs_amount and cogs_amount > 0 and cogs_account and inventory_account:
            # Create COGS voucher
            cogs_voucher_number = f"COGS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cogs_voucher = Voucher(
                voucher_number=cogs_voucher_number,
                voucher_type_id=voucher_type.id,
                voucher_date=transaction_date,
                reference_type='SALES_COGS',
                reference_id=sales_order_id,
                reference_number=sales_order_number,
                narration=f'COGS for Order {sales_order_number}',
                total_amount=cogs_amount,
                is_posted=True,
                tenant_id=tenant_id,
                created_by=username
            )
            session.add(cogs_voucher)
            session.flush()
            
            # Create COGS journal
            cogs_journal = Journal(
                voucher_id=cogs_voucher.id,
                journal_date=transaction_date,
                total_debit=cogs_amount,
                total_credit=cogs_amount,
                tenant_id=tenant_id
            )
            session.add(cogs_journal)
            session.flush()
            
            # Create COGS journal details
            cogs_journal_details = [
                JournalDetail(
                    journal_id=cogs_journal.id,
                    account_id=cogs_account.id,
                    debit_amount=cogs_amount,
                    credit_amount=0,
                    narration=f'COGS - SO {sales_order_number}',
                    tenant_id=tenant_id
                ),
                JournalDetail(
                    journal_id=cogs_journal.id,
                    account_id=inventory_account.id,
                    debit_amount=0,
                    credit_amount=cogs_amount,
                    narration=f'Inventory reduction - SO {sales_order_number}',
                    tenant_id=tenant_id
                )
            ]
            
            for detail in cogs_journal_details:
                session.add(detail)
            
            # Create COGS ledger entries
            cogs_ledger_entries = [
                Ledger(
                    account_id=cogs_account.id,
                    voucher_id=cogs_voucher.id,
                    transaction_date=transaction_date,
                    debit_amount=cogs_amount,
                    credit_amount=0,
                    balance=(cogs_account.current_balance or Decimal('0')) + Decimal(str(cogs_amount)),
                    narration=f'COGS - SO {sales_order_number}',
                    tenant_id=tenant_id
                ),
                Ledger(
                    account_id=inventory_account.id,
                    voucher_id=cogs_voucher.id,
                    transaction_date=transaction_date,
                    debit_amount=0,
                    credit_amount=cogs_amount,
                    balance=(inventory_account.current_balance or Decimal('0')) - Decimal(str(cogs_amount)),
                    narration=f'Inventory reduction - SO {sales_order_number}',
                    tenant_id=tenant_id
                )
            ]
            
            for ledger in cogs_ledger_entries:
                session.add(ledger)
            
            # Update COGS and Inventory balances
            self.account_service.update_account_balance_in_session(session, cogs_account.id, cogs_amount, 'DEBIT')
            self.account_service.update_account_balance_in_session(session, inventory_account.id, cogs_amount, 'CREDIT')
        
        return voucher
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def record_purchase_transaction(self, purchase_order_id, purchase_order_number, amount, transaction_date=None):
        """Record purchase transaction (creates Inventory and AP entries)"""
        with db_manager.get_session() as session:
            return self.record_purchase_transaction_in_session(session, purchase_order_id, purchase_order_number, amount, transaction_date)
    
    def record_purchase_transaction_in_session(self, session, purchase_order_id, purchase_order_number, amount, transaction_date=None):
        """Record purchase transaction within existing session"""
        if not transaction_date:
            transaction_date = datetime.now()
        
        tenant_id = session_manager.get_current_tenant_id()
        username = session_manager.get_current_username()
        
        # Get accounts
        inventory_account = session.query(AccountMaster).filter(
            AccountMaster.code == '1200-INV',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        ap_account = session.query(AccountMaster).filter(
            AccountMaster.code == '2100-AP',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        # Get voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.code == 'PUR',
            VoucherType.tenant_id == tenant_id
        ).first()
        
        if not voucher_type:
            voucher_type = session.query(VoucherType).filter(
                VoucherType.code == 'JV',
                VoucherType.tenant_id == tenant_id
            ).first()
        
        # Create voucher
        voucher_number = f"PUR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        voucher = Voucher(
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=transaction_date,
            reference_type='PURCHASE',
            reference_id=purchase_order_id,
            reference_number=purchase_order_number,
            narration=f'Purchase transaction for Order {purchase_order_number}',
            total_amount=amount,
            is_posted=True,
            tenant_id=tenant_id,
            created_by=username
        )
        session.add(voucher)
        session.flush()
        
        # Create journal
        journal = Journal(
            voucher_id=voucher.id,
            journal_date=transaction_date,
            total_debit=amount,
            total_credit=amount,
            tenant_id=tenant_id
        )
        session.add(journal)
        session.flush()
        
        # Create journal details - Debit Inventory, Credit AP
        journal_details = [
            JournalDetail(
                journal_id=journal.id,
                account_id=inventory_account.id,
                debit_amount=amount,
                credit_amount=0,
                narration=f'Inventory purchased - PO {purchase_order_number}',
                tenant_id=tenant_id
            ),
            JournalDetail(
                journal_id=journal.id,
                account_id=ap_account.id,
                debit_amount=0,
                credit_amount=amount,
                narration=f'Purchase on credit - PO {purchase_order_number}',
                tenant_id=tenant_id
            )
        ]
        
        for detail in journal_details:
            session.add(detail)
        
        # Create ledger entries
        ledger_entries = [
            Ledger(
                account_id=inventory_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=amount,
                credit_amount=0,
                balance=(inventory_account.current_balance or Decimal('0')) + Decimal(str(amount)),
                narration=f'Inventory purchased - PO {purchase_order_number}',
                tenant_id=tenant_id
            ),
            Ledger(
                account_id=ap_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=amount,
                balance=(ap_account.current_balance or Decimal('0')) + Decimal(str(amount)),
                narration=f'Purchase on credit - PO {purchase_order_number}',
                tenant_id=tenant_id
            )
        ]
        
        for ledger in ledger_entries:
            session.add(ledger)
        
        # Update account balances within same session
        self.account_service.update_account_balance_in_session(session, inventory_account.id, amount, 'DEBIT')
        self.account_service.update_account_balance_in_session(session, ap_account.id, amount, 'CREDIT')
        
        return voucher
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def record_waste_transaction(self, waste_id, waste_number, amount, transaction_date=None):
        """Record waste transaction (creates Expense and reduces Inventory)"""
        with db_manager.get_session() as session:
            return self.record_waste_transaction_in_session(session, waste_id, waste_number, amount, transaction_date)
    
    def record_waste_transaction_in_session(self, session, waste_id, waste_number, amount, transaction_date=None):
        """Record waste transaction within existing session"""
        if not transaction_date:
            transaction_date = datetime.now()
        
        tenant_id = session_manager.get_current_tenant_id()
        username = session_manager.get_current_username()
        
        # Get accounts
        inventory_account = session.query(AccountMaster).filter(
            AccountMaster.code == '1200-INV',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        expense_account = session.query(AccountMaster).filter(
            AccountMaster.code == '5200-WASTE',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        if not inventory_account or not expense_account:
            return  # Skip accounting if accounts don't exist
        
        # Get voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.code == 'JV',
            VoucherType.tenant_id == tenant_id
        ).first()
        
        if not voucher_type:
            return  # Skip if no voucher types exist
        
        # Create voucher
        voucher_number = f"WST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        voucher = Voucher(
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=transaction_date,
            reference_type='WASTE',
            reference_id=waste_id,
            reference_number=waste_number,
            narration=f'Product waste - {waste_number}',
            total_amount=amount,
            is_posted=True,
            tenant_id=tenant_id,
            created_by=username
        )
        session.add(voucher)
        session.flush()
        
        # Create journal
        journal = Journal(
            voucher_id=voucher.id,
            journal_date=transaction_date,
            total_debit=amount,
            total_credit=amount,
            tenant_id=tenant_id
        )
        session.add(journal)
        session.flush()
        
        # Create journal details - Debit Expense, Credit Inventory
        journal_details = [
            JournalDetail(
                journal_id=journal.id,
                account_id=expense_account.id,
                debit_amount=amount,
                credit_amount=0,
                narration=f'Product waste expense - {waste_number}',
                tenant_id=tenant_id
            ),
            JournalDetail(
                journal_id=journal.id,
                account_id=inventory_account.id,
                debit_amount=0,
                credit_amount=amount,
                narration=f'Inventory reduction - waste {waste_number}',
                tenant_id=tenant_id
            )
        ]
        
        for detail in journal_details:
            session.add(detail)
        
        # Create ledger entries
        ledger_entries = [
            Ledger(
                account_id=expense_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=amount,
                credit_amount=0,
                balance=expense_account.current_balance + Decimal(str(amount)),
                narration=f'Product waste expense - {waste_number}',
                tenant_id=tenant_id
            ),
            Ledger(
                account_id=inventory_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=amount,
                balance=inventory_account.current_balance - Decimal(str(amount)),
                narration=f'Inventory reduction - waste {waste_number}',
                tenant_id=tenant_id
            )
        ]
        
        for ledger in ledger_entries:
            session.add(ledger)
        
        # Update account balances within same session
        self.account_service.update_account_balance_in_session(session, expense_account.id, amount, 'DEBIT')
        self.account_service.update_account_balance_in_session(session, inventory_account.id, amount, 'CREDIT')
        
        return voucher
    
    def reverse_sales_transaction_in_session(self, session, sales_order_id, sales_order_number, amount, transaction_date=None):
        """Reverse sales transaction within existing session"""
        if not transaction_date:
            transaction_date = datetime.now()
        
        tenant_id = session_manager.get_current_tenant_id()
        username = session_manager.get_current_username()
        
        # Get accounts
        ar_account = session.query(AccountMaster).filter(
            AccountMaster.code == '1100-AR',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        sales_account = session.query(AccountMaster).filter(
            AccountMaster.code == '4100-SALES',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        if not ar_account or not sales_account:
            return  # Skip if accounts don't exist
        
        # Get voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.code == 'JV',
            VoucherType.tenant_id == tenant_id
        ).first()
        
        if not voucher_type:
            return  # Skip if voucher type doesn't exist
        
        # Create reversal voucher
        voucher_number = f"REV-SAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        voucher = Voucher(
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=transaction_date,
            reference_type='SALES_REVERSAL',
            reference_id=sales_order_id,
            reference_number=f"REV-{sales_order_number}",
            narration=f'Sales reversal for Order {sales_order_number}',
            total_amount=amount,
            is_posted=True,
            tenant_id=tenant_id,
            created_by=username
        )
        session.add(voucher)
        session.flush()
        
        # Create journal
        journal = Journal(
            voucher_id=voucher.id,
            journal_date=transaction_date,
            total_debit=amount,
            total_credit=amount,
            tenant_id=tenant_id
        )
        session.add(journal)
        session.flush()
        
        # Create journal details - Credit AR, Debit Sales (reverse of original)
        journal_details = [
            JournalDetail(
                journal_id=journal.id,
                account_id=sales_account.id,
                debit_amount=amount,
                credit_amount=0,
                narration=f'Sales reversal - SO {sales_order_number}',
                tenant_id=tenant_id
            ),
            JournalDetail(
                journal_id=journal.id,
                account_id=ar_account.id,
                debit_amount=0,
                credit_amount=amount,
                narration=f'AR reversal - SO {sales_order_number}',
                tenant_id=tenant_id
            )
        ]
        
        for detail in journal_details:
            session.add(detail)
        
        # Create ledger entries
        ledger_entries = [
            Ledger(
                account_id=sales_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=amount,
                credit_amount=0,
                balance=sales_account.current_balance - Decimal(str(amount)),
                narration=f'Sales reversal - SO {sales_order_number}',
                tenant_id=tenant_id
            ),
            Ledger(
                account_id=ar_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=amount,
                balance=ar_account.current_balance - Decimal(str(amount)),
                narration=f'AR reversal - SO {sales_order_number}',
                tenant_id=tenant_id
            )
        ]
        
        for ledger in ledger_entries:
            session.add(ledger)
        
        # Update account balances within same session (reverse of original)
        self.account_service.update_account_balance_in_session(session, sales_account.id, amount, 'DEBIT')
        self.account_service.update_account_balance_in_session(session, ar_account.id, amount, 'CREDIT')
        
        return voucher
    
    def reverse_purchase_transaction_in_session(self, session, purchase_order_id, purchase_order_number, amount, transaction_date=None):
        """Reverse purchase transaction within existing session"""
        if not transaction_date:
            transaction_date = datetime.now()
        
        tenant_id = session_manager.get_current_tenant_id()
        username = session_manager.get_current_username()
        
        # Get accounts
        inventory_account = session.query(AccountMaster).filter(
            AccountMaster.code == '1200-INV',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        ap_account = session.query(AccountMaster).filter(
            AccountMaster.code == '2100-AP',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        if not inventory_account or not ap_account:
            return  # Skip if accounts don't exist
        
        # Get voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.code == 'JV',
            VoucherType.tenant_id == tenant_id
        ).first()
        
        if not voucher_type:
            return  # Skip if voucher type doesn't exist
        
        # Create reversal voucher
        voucher_number = f"REV-PUR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        voucher = Voucher(
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=transaction_date,
            reference_type='PURCHASE_REVERSAL',
            reference_id=purchase_order_id,
            reference_number=f"REV-{purchase_order_number}",
            narration=f'Purchase reversal for Order {purchase_order_number}',
            total_amount=amount,
            is_posted=True,
            tenant_id=tenant_id,
            created_by=username
        )
        session.add(voucher)
        session.flush()
        
        # Create journal
        journal = Journal(
            voucher_id=voucher.id,
            journal_date=transaction_date,
            total_debit=amount,
            total_credit=amount,
            tenant_id=tenant_id
        )
        session.add(journal)
        session.flush()
        
        # Create journal details - Credit Inventory, Debit AP (reverse of original)
        journal_details = [
            JournalDetail(
                journal_id=journal.id,
                account_id=ap_account.id,
                debit_amount=amount,
                credit_amount=0,
                narration=f'AP reversal - PO {purchase_order_number}',
                tenant_id=tenant_id
            ),
            JournalDetail(
                journal_id=journal.id,
                account_id=inventory_account.id,
                debit_amount=0,
                credit_amount=amount,
                narration=f'Inventory reversal - PO {purchase_order_number}',
                tenant_id=tenant_id
            )
        ]
        
        for detail in journal_details:
            session.add(detail)
        
        # Create ledger entries
        ledger_entries = [
            Ledger(
                account_id=ap_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=amount,
                credit_amount=0,
                balance=ap_account.current_balance - Decimal(str(amount)),
                narration=f'AP reversal - PO {purchase_order_number}',
                tenant_id=tenant_id
            ),
            Ledger(
                account_id=inventory_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=amount,
                balance=inventory_account.current_balance - Decimal(str(amount)),
                narration=f'Inventory reversal - PO {purchase_order_number}',
                tenant_id=tenant_id
            )
        ]
        
        for ledger in ledger_entries:
            session.add(ledger)
        
        # Update account balances within same session (reverse of original)
        self.account_service.update_account_balance_in_session(session, ap_account.id, amount, 'DEBIT')
        self.account_service.update_account_balance_in_session(session, inventory_account.id, amount, 'CREDIT')
        
        return voucher
    
    # ==================== NEW PAYMENT STRUCTURE METHODS ====================
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def create_payment(self, payment_data: dict):
        """Create a new payment with details"""
        from modules.account_module.models.payment_entity import Payment, PaymentDetail
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            # Check if payment number already exists
            existing = session.query(Payment).filter(
                Payment.tenant_id == tenant_id,
                Payment.payment_number == payment_data.get('payment_number'),
                Payment.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Payment number '{payment_data.get('payment_number')}' already exists")
            
            # Extract details from payment data
            details_data = payment_data.pop('details', [])
            
            # Create payment header
            payment = Payment(
                tenant_id=tenant_id,
                payment_number=payment_data.get('payment_number'),
                payment_date=payment_data.get('payment_date'),
                payment_type=payment_data.get('payment_type'),
                party_type=payment_data.get('party_type'),
                party_id=payment_data.get('party_id'),
                party_name=payment_data.get('party_name'),
                party_phone=payment_data.get('party_phone'),
                base_currency_id=payment_data.get('base_currency_id'),
                foreign_currency_id=payment_data.get('foreign_currency_id'),
                exchange_rate=payment_data.get('exchange_rate', 1),
                total_amount_base=payment_data.get('total_amount_base'),
                total_amount_foreign=payment_data.get('total_amount_foreign'),
                tds_amount_base=payment_data.get('tds_amount_base', 0),
                advance_amount_base=payment_data.get('advance_amount_base', 0),
                status=payment_data.get('status', 'DRAFT'),
                reference_number=payment_data.get('reference_number'),
                remarks=payment_data.get('remarks'),
                tags=payment_data.get('tags'),
                created_by=username,
                updated_by=username
            )
            
            session.add(payment)
            session.flush()  # Get payment ID
            
            # Create payment details
            for detail_data in details_data:
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
            
            session.commit()
            session.refresh(payment)
            
            return self.get_payment_by_id(payment.id)
    
    def _apply_payment_filters(self, query, filters):
        """Helper method to handle the filtering logic"""
        from modules.account_module.models.payment_entity import Payment
        
        # Mapping simple params to query filters
        # format: { 'param_name': column_attribute }
        multi_match_fields = {
            'payment_type': Payment.payment_type,
            'party_type': Payment.party_type,
            'status': Payment.status,
        }

        # Handle List or Single Value filters (IN vs ==)
        for param, column in multi_match_fields.items():
            val = filters.get(param)
            if val:
                query = query.filter(column.in_(val) if isinstance(val, list) else column == val)

        # Handle Search (OR logic)
        search = filters.get('search')
        if search:
            pattern = f"%{search}%"
            query = query.filter(or_(
                Payment.payment_number.ilike(pattern),
                Payment.reference_number.ilike(pattern),
                Payment.remarks.ilike(pattern)
            ))

        # Handle Dates
        if filters.get('date_from'):
            query = query.filter(Payment.payment_date >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(Payment.payment_date <= filters['date_to'])

        # Handle Booleans/IDs (direct matches)
        if filters.get('is_reconciled') is not None:
            query = query.filter(Payment.is_reconciled == filters['is_reconciled'])
        if filters.get('branch_id') is not None:
            query = query.filter(Payment.branch_id == filters['branch_id'])
        if filters.get('is_reversal') is not None:
            query = query.filter(Payment.is_reversal == filters['is_reversal'])
        if filters.get('is_allocated') is not None:
            if filters.get('is_allocated') is True:
                # If is_allocated is true, filter for 0 amount
                query = query.filter(Payment.unallocated_amount_base == 0)
            elif filters.get('is_allocated') is False:
                # Optional: logic for when is_allocated is False (e.g., amount > 0)
                query = query.filter(Payment.unallocated_amount_base > 0)

        return query

    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def get_all_payments(self, page=1, page_size=100, 
                        include_details=True, 
                        include_allocations=True, 
                        **filters):
        """Refactored: Get all payments with explicit detail flags"""
        from modules.account_module.models.payment_entity import Payment
        import math
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            # 1. Base Query
            query = session.query(Payment).filter(
                Payment.tenant_id == tenant_id,
                Payment.is_deleted == False
            )
            
            # 2. Apply Dynamic Filters (Using the helper from the previous response)
            query = self._apply_payment_filters(query, filters)
            
            # 3. Get total count
            total = query.count()
            
            # 4. Define Eager Loading based on flags
            load_options = []
            if include_details:
                load_options.append(selectinload(Payment.payment_details))
            if include_allocations:
                load_options.append(selectinload(Payment.payment_allocations))
            
            # 5. Apply Pagination & Ordering
            query = query.order_by(Payment.payment_date.desc(), Payment.id.desc())
            offset = (page - 1) * page_size
            
            payments = query.options(*load_options).offset(offset).limit(page_size).all()
            
            return {
                'total': total,
                'page': page,
                'per_page': page_size,
                'total_pages': math.ceil(total / page_size) if total > 0 else 0,
                # Ensure flags are passed to the dict converter
                'data': [
                    self._payment_to_dict(
                        p, 
                        include_details=include_details, 
                        include_allocations=include_allocations
                    ) for p in payments
                ]
            }
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def get_payment_by_id(self, payment_id: int):
        """Get a specific payment by ID with details"""
        from modules.account_module.models.payment_entity import Payment
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            payment = session.query(Payment).filter(
                Payment.id == payment_id,
                Payment.tenant_id == tenant_id,
                Payment.is_deleted == False
            ).first()
            
            if not payment:
                return None
            
            return self._payment_to_dict(payment, include_details=True)
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def update_payment(self, payment_id: int, payment_data: dict):
        """Update an existing payment"""
        from modules.account_module.models.payment_entity import Payment, PaymentDetail
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            payment = session.query(Payment).filter(
                Payment.id == payment_id,
                Payment.tenant_id == tenant_id,
                Payment.is_deleted == False
            ).first()
            
            if not payment:
                return None
            
            # Check if payment number changed and is unique
            if 'payment_number' in payment_data and payment_data['payment_number'] != payment.payment_number:
                existing = session.query(Payment).filter(
                    Payment.tenant_id == tenant_id,
                    Payment.payment_number == payment_data['payment_number'],
                    Payment.id != payment_id,
                    Payment.is_deleted == False
                ).first()
                
                if existing:
                    raise ValueError(f"Payment number '{payment_data['payment_number']}' already exists")
            
            # Extract details if present
            details_data = payment_data.pop('details', None)
            
            # Update header fields
            for field in ['payment_number', 'payment_date', 'payment_type', 'party_type', 'party_id',
                         'party_name', 'party_phone',
                         'base_currency_id', 'foreign_currency_id', 'exchange_rate',
                         'total_amount_base', 'total_amount_foreign',
                         'tds_amount_base', 'advance_amount_base', 'status',
                         'reference_number', 'remarks', 'tags']:
                if field in payment_data:
                    setattr(payment, field, payment_data[field])
            
            payment.updated_by = username
            
            # Update details if provided
            if details_data is not None:
                # Delete existing details
                session.query(PaymentDetail).filter(
                    PaymentDetail.payment_id == payment_id
                ).delete()
                
                # Add new details
                for detail_data in details_data:
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
            
            session.commit()
            session.refresh(payment)
            
            return self.get_payment_by_id(payment.id)
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def delete_payment(self, payment_id: int):
        """Soft delete a payment"""
        from modules.account_module.models.payment_entity import Payment
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            payment = session.query(Payment).filter(
                Payment.id == payment_id,
                Payment.tenant_id == tenant_id,
                Payment.is_deleted == False
            ).first()
            
            if not payment:
                return False
            
            # Check if payment can be deleted (only DRAFT or CANCELLED)
            if payment.status not in ['DRAFT', 'CANCELLED']:
                raise ValueError(f"Cannot delete payment with status '{payment.status}'. Only DRAFT or CANCELLED payments can be deleted.")
            
            payment.is_deleted = True
            payment.is_active = False
            payment.updated_by = username
            
            session.commit()
            return True
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def reconcile_payment(self, payment_id: int, reconciled_at: datetime = None):
        """Reconcile a payment"""
        from modules.account_module.models.payment_entity import Payment
    
    # ==================== PATIENT ADVANCE & TEST INVOICE METHODS ====================
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def record_test_invoice_transaction(self, session, test_invoice_id, invoice_number, 
                                       taxable_amount, cgst_amount, sgst_amount, igst_amount, 
                                       final_amount, transaction_date=None):
        """Record test invoice transaction (AR Dr, Diagnostic Revenue Cr, GST Cr)"""
        if not transaction_date:
            transaction_date = datetime.now()
        
        tenant_id = session_manager.get_current_tenant_id()
        username = session_manager.get_current_username()
        
        # Get accounts
        ar_account = session.query(AccountMaster).filter(
            AccountMaster.code == '1100-AR',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        diagnostic_revenue = session.query(AccountMaster).filter(
            AccountMaster.code == '4300-DIAGNOSTIC',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        cgst_output = session.query(AccountMaster).filter(
            AccountMaster.code == '2310-GST-CGST-OUT',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        sgst_output = session.query(AccountMaster).filter(
            AccountMaster.code == '2320-GST-SGST-OUT',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        igst_output = session.query(AccountMaster).filter(
            AccountMaster.code == '2330-GST-IGST-OUT',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        # Get voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.code == 'SALES',
            VoucherType.tenant_id == tenant_id
        ).first()
        
        if not voucher_type:
            voucher_type = session.query(VoucherType).filter(
                VoucherType.code == 'JOURNAL',
                VoucherType.tenant_id == tenant_id
            ).first()
        
        # Create voucher
        voucher_number = f"TINV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        voucher = Voucher(
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=transaction_date,
            reference_type='TEST_INVOICE',
            reference_id=test_invoice_id,
            reference_number=invoice_number,
            narration=f'Test invoice {invoice_number}',
            total_amount=final_amount,
            is_posted=True,
            tenant_id=tenant_id,
            created_by=username
        )
        session.add(voucher)
        session.flush()
        
        # Create journal
        journal = Journal(
            voucher_id=voucher.id,
            journal_date=transaction_date,
            total_debit=final_amount,
            total_credit=final_amount,
            tenant_id=tenant_id
        )
        session.add(journal)
        session.flush()
        
        # Create journal details
        journal_details = [
            JournalDetail(
                journal_id=journal.id,
                account_id=ar_account.id,
                debit_amount=final_amount,
                credit_amount=0,
                narration=f'Test invoice {invoice_number}',
                tenant_id=tenant_id
            ),
            JournalDetail(
                journal_id=journal.id,
                account_id=diagnostic_revenue.id,
                debit_amount=0,
                credit_amount=taxable_amount,
                narration=f'Diagnostic revenue - {invoice_number}',
                tenant_id=tenant_id
            )
        ]
        
        if cgst_amount > 0:
            journal_details.append(JournalDetail(
                journal_id=journal.id,
                account_id=cgst_output.id,
                debit_amount=0,
                credit_amount=cgst_amount,
                narration=f'CGST - {invoice_number}',
                tenant_id=tenant_id
            ))
        
        if sgst_amount > 0:
            journal_details.append(JournalDetail(
                journal_id=journal.id,
                account_id=sgst_output.id,
                debit_amount=0,
                credit_amount=sgst_amount,
                narration=f'SGST - {invoice_number}',
                tenant_id=tenant_id
            ))
        
        if igst_amount > 0:
            journal_details.append(JournalDetail(
                journal_id=journal.id,
                account_id=igst_output.id,
                debit_amount=0,
                credit_amount=igst_amount,
                narration=f'IGST - {invoice_number}',
                tenant_id=tenant_id
            ))
        
        for detail in journal_details:
            session.add(detail)
        
        # Create ledger entries
        ledger_entries = [
            Ledger(
                account_id=ar_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=final_amount,
                credit_amount=0,
                balance=ar_account.current_balance + Decimal(str(final_amount)),
                narration=f'Test invoice {invoice_number}',
                tenant_id=tenant_id
            ),
            Ledger(
                account_id=diagnostic_revenue.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=taxable_amount,
                balance=diagnostic_revenue.current_balance + Decimal(str(taxable_amount)),
                narration=f'Diagnostic revenue - {invoice_number}',
                tenant_id=tenant_id
            )
        ]
        
        if cgst_amount > 0:
            ledger_entries.append(Ledger(
                account_id=cgst_output.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=cgst_amount,
                balance=cgst_output.current_balance + Decimal(str(cgst_amount)),
                narration=f'CGST - {invoice_number}',
                tenant_id=tenant_id
            ))
        
        if sgst_amount > 0:
            ledger_entries.append(Ledger(
                account_id=sgst_output.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=sgst_amount,
                balance=sgst_output.current_balance + Decimal(str(sgst_amount)),
                narration=f'SGST - {invoice_number}',
                tenant_id=tenant_id
            ))
        
        if igst_amount > 0:
            ledger_entries.append(Ledger(
                account_id=igst_output.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=igst_amount,
                balance=igst_output.current_balance + Decimal(str(igst_amount)),
                narration=f'IGST - {invoice_number}',
                tenant_id=tenant_id
            ))
        
        for ledger in ledger_entries:
            session.add(ledger)
        
        # Update account balances
        self.account_service.update_account_balance_in_session(session, ar_account.id, final_amount, 'DEBIT')
        self.account_service.update_account_balance_in_session(session, diagnostic_revenue.id, taxable_amount, 'CREDIT')
        if cgst_amount > 0:
            self.account_service.update_account_balance_in_session(session, cgst_output.id, cgst_amount, 'CREDIT')
        if sgst_amount > 0:
            self.account_service.update_account_balance_in_session(session, sgst_output.id, sgst_amount, 'CREDIT')
        if igst_amount > 0:
            self.account_service.update_account_balance_in_session(session, igst_output.id, igst_amount, 'CREDIT')
        
        return voucher
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def record_advance_receipt(self, session, payment_id, payment_number, amount, transaction_date=None):
        """Record patient advance receipt (Cash Dr, Patient Advance Cr)"""
        if not transaction_date:
            transaction_date = datetime.now()
        
        tenant_id = session_manager.get_current_tenant_id()
        username = session_manager.get_current_username()
        
        # Get accounts
        cash_account = session.query(AccountMaster).filter(
            AccountMaster.code == '1010-CASH',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        advance_account = session.query(AccountMaster).filter(
            AccountMaster.code == '2200-PAT-ADV',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        # Get voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.code == 'RECEIPT',
            VoucherType.tenant_id == tenant_id
        ).first()
        
        # Create voucher
        voucher_number = f"ADV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        voucher = Voucher(
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=transaction_date,
            reference_type='ADVANCE_RECEIPT',
            reference_id=payment_id,
            reference_number=payment_number,
            narration=f'Patient advance - {payment_number}',
            total_amount=amount,
            is_posted=True,
            tenant_id=tenant_id,
            created_by=username
        )
        session.add(voucher)
        session.flush()
        
        # Create journal
        journal = Journal(
            voucher_id=voucher.id,
            journal_date=transaction_date,
            total_debit=amount,
            total_credit=amount,
            tenant_id=tenant_id
        )
        session.add(journal)
        session.flush()
        
        # Create journal details
        journal_details = [
            JournalDetail(
                journal_id=journal.id,
                account_id=cash_account.id,
                debit_amount=amount,
                credit_amount=0,
                narration=f'Advance received - {payment_number}',
                tenant_id=tenant_id
            ),
            JournalDetail(
                journal_id=journal.id,
                account_id=advance_account.id,
                debit_amount=0,
                credit_amount=amount,
                narration=f'Patient advance liability - {payment_number}',
                tenant_id=tenant_id
            )
        ]
        
        for detail in journal_details:
            session.add(detail)
        
        # Create ledger entries
        ledger_entries = [
            Ledger(
                account_id=cash_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=amount,
                credit_amount=0,
                balance=cash_account.current_balance + Decimal(str(amount)),
                narration=f'Advance received - {payment_number}',
                tenant_id=tenant_id
            ),
            Ledger(
                account_id=advance_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=amount,
                balance=advance_account.current_balance + Decimal(str(amount)),
                narration=f'Patient advance liability - {payment_number}',
                tenant_id=tenant_id
            )
        ]
        
        for ledger in ledger_entries:
            session.add(ledger)
        
        # Update account balances
        self.account_service.update_account_balance_in_session(session, cash_account.id, amount, 'DEBIT')
        self.account_service.update_account_balance_in_session(session, advance_account.id, amount, 'CREDIT')
        
        return voucher
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def record_advance_allocation(self, session, allocation_id, payment_number, invoice_number, 
                                 amount, transaction_date=None):
        """Record advance allocation to invoice (Patient Advance Dr, AR Cr)"""
        if not transaction_date:
            transaction_date = datetime.now()
        
        tenant_id = session_manager.get_current_tenant_id()
        username = session_manager.get_current_username()
        
        # Get accounts
        advance_account = session.query(AccountMaster).filter(
            AccountMaster.code == '2200-PAT-ADV',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        ar_account = session.query(AccountMaster).filter(
            AccountMaster.code == '1100-AR',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        # Get voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.code == 'JOURNAL',
            VoucherType.tenant_id == tenant_id
        ).first()
        
        # Create voucher
        voucher_number = f"ALLOC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        voucher = Voucher(
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=transaction_date,
            reference_type='ADVANCE_ALLOCATION',
            reference_id=allocation_id,
            reference_number=f"{payment_number}-{invoice_number}",
            narration=f'Advance allocated to {invoice_number}',
            total_amount=amount,
            is_posted=True,
            tenant_id=tenant_id,
            created_by=username
        )
        session.add(voucher)
        session.flush()
        
        # Create journal
        journal = Journal(
            voucher_id=voucher.id,
            journal_date=transaction_date,
            total_debit=amount,
            total_credit=amount,
            tenant_id=tenant_id
        )
        session.add(journal)
        session.flush()
        
        # Create journal details
        journal_details = [
            JournalDetail(
                journal_id=journal.id,
                account_id=advance_account.id,
                debit_amount=amount,
                credit_amount=0,
                narration=f'Advance adjusted - {invoice_number}',
                tenant_id=tenant_id
            ),
            JournalDetail(
                journal_id=journal.id,
                account_id=ar_account.id,
                debit_amount=0,
                credit_amount=amount,
                narration=f'AR reduced - {invoice_number}',
                tenant_id=tenant_id
            )
        ]
        
        for detail in journal_details:
            session.add(detail)
        
        # Create ledger entries
        ledger_entries = [
            Ledger(
                account_id=advance_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=amount,
                credit_amount=0,
                balance=advance_account.current_balance - Decimal(str(amount)),
                narration=f'Advance adjusted - {invoice_number}',
                tenant_id=tenant_id
            ),
            Ledger(
                account_id=ar_account.id,
                voucher_id=voucher.id,
                transaction_date=transaction_date,
                debit_amount=0,
                credit_amount=amount,
                balance=ar_account.current_balance - Decimal(str(amount)),
                narration=f'AR reduced - {invoice_number}',
                tenant_id=tenant_id
            )
        ]
        
        for ledger in ledger_entries:
            session.add(ledger)
        
        # Update account balances
        self.account_service.update_account_balance_in_session(session, advance_account.id, amount, 'DEBIT')
        self.account_service.update_account_balance_in_session(session, ar_account.id, amount, 'CREDIT')
        
        return voucher
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            payment = session.query(Payment).filter(
                Payment.id == payment_id,
                Payment.tenant_id == tenant_id,
                Payment.is_deleted == False
            ).first()
            
            if not payment:
                return None
            
            if payment.is_reconciled:
                raise ValueError("Payment is already reconciled")
            
            payment.is_reconciled = True
            payment.reconciled_at = reconciled_at or datetime.utcnow()
            payment.reconciled_by = username
            payment.status = 'RECONCILED'
            payment.updated_by = username
            
            session.commit()
            session.refresh(payment)
            
            return self._payment_to_dict(payment, include_details=False)
    
    def _get_configured_account(self, session, tenant_id, config_code):
        """Get configured account ID for a given configuration code"""
        from modules.account_module.models.account_configuration_entity import AccountConfiguration
        from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey
        
        config_key = session.query(AccountConfigurationKey).filter(
            AccountConfigurationKey.code == config_code,
            AccountConfigurationKey.is_active == True,
            AccountConfigurationKey.is_deleted == False
        ).first()
        
        if not config_key:
            raise ValueError(f"Account configuration key '{config_code}' not found")
        
        config = session.query(AccountConfiguration).filter(
            AccountConfiguration.tenant_id == tenant_id,
            AccountConfiguration.config_key_id == config_key.id,
            AccountConfiguration.is_deleted == False
        ).first()
        
        if not config:
            if config_key.default_account_id:
                return config_key.default_account_id
            raise ValueError(f"Account configuration for '{config_code}' not found for tenant {tenant_id}")
        
        return config.account_id
    
    def _get_or_create_party_account(self, session, tenant_id, party_type, party_id, username):
        """Get or create account master for customer/vendor/patient"""
        # 1. Define the configurations for each party type
        configs = {
            'CUSTOMER': {
                'model': Customer,
                'group_code': 'ASET',
                'acc_type': 'REVENUE',
                'sys_prefix': 'CUSTOMER',
                'acc_prefix': 'AR',
                'name_func': lambda obj: f"{obj.name} - Receivable",
                'desc_func': lambda obj: f"Account receivable for customer {obj.name}",
                'filter_attr': 'is_active'
            },
            'SUPPLIER': {
                'model': Supplier,
                'group_code': 'LIAB',
                'acc_type': 'LIABILITY',
                'sys_prefix': 'VENDOR',
                'acc_prefix': 'AP',
                'name_func': lambda obj: f"{obj.name} - Payable",
                'desc_func': lambda obj: f"Account payable for supplier {obj.name}",
                'filter_attr': 'is_deleted',
                'filter_val': False
            },
            'PATIENT': {
                'model': Patient,
                'group_code': 'ASET',
                'acc_type': 'REVENUE',
                'sys_prefix': 'PATIENT',
                'acc_prefix': 'PAR',
                'name_func': lambda obj: f"{obj.first_name} {obj.last_name} - Receivable",
                'desc_func': lambda obj: f"Account receivable for patient {obj.first_name} {obj.last_name}",
                'filter_attr': 'is_active'
            }
        }

        if party_type not in configs:
            raise ValueError(f"Unsupported party type: {party_type}")

        cfg = configs[party_type]
        
        # 2. Fetch the Entity (Customer/Supplier/Patient)
        filter_val = cfg.get('filter_val', True)
        entity = session.query(cfg['model']).filter(
            cfg['model'].id == party_id,
            cfg['model'].tenant_id == tenant_id,
            getattr(cfg['model'], cfg['filter_attr']) == filter_val
        ).first()

        if not entity:
            raise ValueError(f"{party_type.title()} with ID {party_id} not found")

        # 3. Check if Account already exists
        system_code = f"{cfg['sys_prefix']}_{party_id}"
        account = session.query(AccountMaster).filter(
            AccountMaster.tenant_id == tenant_id,
            AccountMaster.system_code == system_code,
            AccountMaster.is_deleted == False
        ).first()

        if account:
            return account.id

        # 4. Fetch Account Group
        group = session.query(AccountGroup).filter(
            AccountGroup.tenant_id == tenant_id,
            AccountGroup.code == cfg['group_code'],
            AccountGroup.is_active == True
        ).first()

        if not group:
            raise ValueError(f"{cfg['group_code']} account group not found")

        # 5. Create New Account
        new_account = AccountMaster(
            tenant_id=tenant_id,
            account_group_id=group.id,
            account_type=cfg['acc_type'],
            code=f"{cfg['acc_prefix']}-{party_id:06d}",
            name=cfg['name_func'](entity),
            description=cfg['desc_func'](entity),
            system_code=system_code,
            is_system_account=False,
            opening_balance=Decimal(0),
            current_balance=Decimal(0),
            created_by=username,
            updated_by=username
        )

        session.add(new_account)
        session.flush()
        return new_account.id



    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def create_invoice_payment(self, payment_data: dict):
        """Create payment for invoice with proper voucher entries"""
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                # Check if payment number already exists
                existing = session.query(Payment).filter(
                    Payment.tenant_id == tenant_id,
                    Payment.payment_number == payment_data.get('payment_number'),
                    Payment.is_deleted == False
                ).first()
                
                if existing:
                    raise ValueError(f"Payment number '{payment_data.get('payment_number')}' already exists")
                
                # Extract details from payment data
                details_data = payment_data.pop('details', [])
                
                # Create payment header
                payment = Payment(
                    tenant_id=tenant_id,
                    payment_number=payment_data.get('payment_number'),
                    payment_date=payment_data.get('payment_date', datetime.utcnow()),
                    payment_type=payment_data.get('payment_type'),
                    party_type=payment_data.get('party_type'),
                    party_id=payment_data.get('party_id'),
                    party_name=payment_data.get('party_name'),
                    party_phone=payment_data.get('party_phone'),
                    base_currency_id=payment_data.get('base_currency_id'),
                    foreign_currency_id=payment_data.get('foreign_currency_id'),
                    exchange_rate=payment_data.get('exchange_rate', 1),
                    total_amount_base=payment_data.get('total_amount_base'),
                    total_amount_foreign=payment_data.get('total_amount_foreign'),
                    status='POSTED',
                    reference_number=payment_data.get('reference_number'),
                    remarks=payment_data.get('remarks'),
                    created_by=username,
                    updated_by=username
                )
                
                session.add(payment)
                session.flush()
                
                # Create payment details
                for detail_data in details_data:
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
                
                # Create payment voucher
                voucher = self._create_invoice_payment_voucher(session, tenant_id, username, payment, details_data)
                payment.voucher_id = voucher.id
                
                session.commit()
                session.refresh(payment)
                
                return self._payment_to_dict(payment, include_details=True)
                
            except Exception as e:
                session.rollback()
                raise
    
    def _create_invoice_payment_voucher(self, session, tenant_id, username, payment, details_data):
        """Create accounting voucher for payment"""
        voucher_type_code = 'RECEIPT' if payment.payment_type == 'RECEIPT' else 'PAYMENT'
        voucher_type = session.query(VoucherType).filter(
            VoucherType.tenant_id == tenant_id,
            VoucherType.code == voucher_type_code,
            VoucherType.is_active == True,
            VoucherType.is_deleted == False
        ).first()
        
        if not voucher_type:
            raise ValueError(f"{voucher_type_code} voucher type not configured")
        
        voucher_number = f"{voucher_type_code[:3]}-{payment.payment_number}"
        
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
            reference_type='PAYMENT',
            reference_id=payment.id,
            reference_number=payment.payment_number,
            narration=f"{payment.payment_type} {payment.payment_number} - {payment.remarks or ''}",
            is_posted=True,
            created_by=username,
            updated_by=username
        )
        
        session.add(voucher)
        session.flush()
        
        # Get party account
        party_account_id = self._get_or_create_party_account(session, tenant_id, payment.party_type, payment.party_id, username)
        
        line_no = 1
        
        if payment.payment_type == 'RECEIPT':
            # Debit: Bank/Cash, Credit: Customer
            for detail_data in details_data:
                payment_mode = detail_data.get('payment_mode', 'CASH')
                amount = Decimal(str(detail_data.get('amount_base', 0)))
                
                if detail_data.get('account_id'):
                    payment_account_id = detail_data.get('account_id')
                else:
                    try:
                        payment_account_id = self._get_configured_account(session, tenant_id, 'CASH' if payment_mode == 'CASH' else 'BANK')
                    except ValueError:
                        raise ValueError(f"Payment account not configured for mode {payment_mode}")
                
                payment_line = VoucherLine(
                    tenant_id=tenant_id,
                    voucher_id=voucher.id,
                    line_no=line_no,
                    account_id=payment_account_id,
                    description=f"{payment_mode} receipt",
                    debit_base=amount,
                    credit_base=Decimal(0),
                    reference_type='PAYMENT',
                    reference_id=payment.id,
                    created_by=username,
                    updated_by=username
                )
                session.add(payment_line)
                line_no += 1
            
            # Credit: Customer Account
            party_line = VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=party_account_id,
                description=f"Receipt from customer - {payment.reference_number}",
                debit_base=Decimal(0),
                credit_base=payment.total_amount_base,
                reference_type='PAYMENT',
                reference_id=payment.id,
                created_by=username,
                updated_by=username
            )
            session.add(party_line)
            
        else:  # PAYMENT
            # Debit: Supplier, Credit: Bank/Cash
            party_line = VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=party_account_id,
                description=f"Payment to supplier - {payment.reference_number}",
                debit_base=payment.total_amount_base,
                credit_base=Decimal(0),
                reference_type='PAYMENT',
                reference_id=payment.id,
                created_by=username,
                updated_by=username
            )
            session.add(party_line)
            line_no += 1
            
            for detail_data in details_data:
                payment_mode = detail_data.get('payment_mode', 'CASH')
                amount = Decimal(str(detail_data.get('amount_base', 0)))
                
                if detail_data.get('account_id'):
                    payment_account_id = detail_data.get('account_id')
                else:
                    try:
                        payment_account_id = self._get_configured_account(session, tenant_id, 'CASH' if payment_mode == 'CASH' else 'BANK')
                    except ValueError:
                        raise ValueError(f"Payment account not configured for mode {payment_mode}")
                
                payment_line = VoucherLine(
                    tenant_id=tenant_id,
                    voucher_id=voucher.id,
                    line_no=line_no,
                    account_id=payment_account_id,
                    description=f"{payment_mode} payment",
                    debit_base=Decimal(0),
                    credit_base=amount,
                    reference_type='PAYMENT',
                    reference_id=payment.id,
                    created_by=username,
                    updated_by=username
                )
                session.add(payment_line)
                line_no += 1
        
        return voucher
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def update_invoice_payment_status(self, invoice_type, invoice_id, payment_amount):
        """Update invoice payment status after payment is made"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            if invoice_type == 'SALES':
                from modules.inventory_module.models.sales_invoice_entity import SalesInvoice
                invoice = session.query(SalesInvoice).filter(
                    SalesInvoice.id == invoice_id,
                    SalesInvoice.tenant_id == tenant_id,
                    SalesInvoice.is_deleted == False
                ).first()
            elif invoice_type == 'PURCHASE':
                from modules.inventory_module.models.purchase_invoice_entity import PurchaseInvoice
                invoice = session.query(PurchaseInvoice).filter(
                    PurchaseInvoice.id == invoice_id,
                    PurchaseInvoice.tenant_id == tenant_id,
                    PurchaseInvoice.is_deleted == False
                ).first()
            else:
                raise ValueError(f"Unsupported invoice type: {invoice_type}")
            
            if not invoice:
                raise ValueError(f"{invoice_type} invoice with ID {invoice_id} not found")
            
            # Update payment amounts
            invoice.paid_amount_base = (invoice.paid_amount_base or Decimal(0)) + Decimal(str(payment_amount))
            invoice.balance_amount_base = invoice.total_amount_base - invoice.paid_amount_base
            
            # Update status based on payment alignment
            if invoice.balance_amount_base <= 0:
                invoice.status = 'PAID'
            elif invoice.paid_amount_base > 0:
                invoice.status = 'PARTIALLY_PAID'
            else:
                invoice.status = 'POSTED'
            
            invoice.updated_by = username
            invoice.updated_at = datetime.utcnow()
            
            session.commit()
            
            return {
                'invoice_id': invoice.id,
                'status': invoice.status,
                'paid_amount': float(invoice.paid_amount_base),
                'balance_amount': float(invoice.balance_amount_base)
            }

    def _payment_to_dict(self, payment, include_details=True,include_allocations=False):
        """Convert payment entity to dictionary"""
        result = {
            'id': payment.id,
            'payment_number': payment.payment_number,
            'payment_date': payment.payment_date,
            'payment_type': payment.payment_type,
            'party_type': payment.party_type,
            'party_id': payment.party_id,
            'party_name': payment.party_name,
            'party_phone': payment.party_phone,
            'base_currency_id': payment.base_currency_id,
            'foreign_currency_id': payment.foreign_currency_id,
            'exchange_rate': payment.exchange_rate,
            'total_amount_base': payment.total_amount_base,
            'total_amount_foreign': payment.total_amount_foreign,
            'allocated_amount_base': payment.allocated_amount_base,
            'unallocated_amount_base': payment.unallocated_amount_base,
            'tds_amount_base': payment.tds_amount_base,
            'advance_amount_base': payment.advance_amount_base,
            'is_refund': payment.is_refund,
            'status': payment.status,
            'voucher_id': payment.voucher_id,
            'reference_number': payment.reference_number,
            'remarks': payment.remarks,
            'tags': payment.tags,
            'is_reconciled': payment.is_reconciled,
            'reconciled_at': payment.reconciled_at,
            'reconciled_by': payment.reconciled_by,
            'created_at': payment.created_at,
            'created_by': payment.created_by,
            'updated_at': payment.updated_at,
            'updated_by': payment.updated_by,
            'is_active': payment.is_active,
            'is_deleted': payment.is_deleted
        }
        
        # 2. Map Payment Details (Lines)
        if include_details:
            result['details'] = [self._detail_to_dict(detail) for detail in payment.payment_details]
        else:
            result['details'] = []

        # 3. Map Payment Allocations
        if include_allocations:
            result['allocations'] = [self._allocation_to_dict(allocations) for allocations in payment.payment_allocations]
        else:
            result['allocations'] = []
        
        return result
    
    def _detail_to_dict(self, detail):
        """Convert payment detail entity to dictionary"""
        return {
            'id': detail.id,
            'line_no': detail.line_no,
            'payment_mode': detail.payment_mode,
            'bank_account_id': detail.bank_account_id,
            'instrument_number': detail.instrument_number,
            'instrument_date': detail.instrument_date,
            'bank_name': detail.bank_name,
            'branch_name': detail.branch_name,
            'ifsc_code': detail.ifsc_code,
            'transaction_reference': detail.transaction_reference,
            'amount_base': detail.amount_base,
            'amount_foreign': detail.amount_foreign,
            'account_id': detail.account_id,
            'description': detail.description,
            'gateway_fee_base': getattr(detail, 'gateway_fee_base', None)
        }
    
    def _allocation_to_dict(self, detail):
        """Convert payment allocations entity to dictionary"""
        return {
            'id': detail.id,
            'document_type': detail.document_type,
            'document_id': detail.document_id,
            'document_number': detail.document_number,
            'allocated_amount_base': detail.allocated_amount_base,
            #'allocated_amount_foreign': detail.allocated_amount_foreign,
            'discount_amount_base': detail.discount_amount_base,
            'adjustment_amount_base': detail.adjustment_amount_base,
            'allocation_date': detail.allocation_date,
            'remarks': detail.remarks,
            'created_at':detail.created_at,
            'created_by':detail.created_by,
            'updated_at':detail.updated_at,
            'updated_by':detail.updated_by,
            #'is_deleted':detail.is_deleted
        }
    

    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def create_advance_payment(self, payment_number: str, party_id: int, party_type: str, 
                              party_name: str, party_phone: str, amount: Decimal, payment_mode: str = 'CASH', 
                              instrument_number: str = None, instrument_date: date = None,
                              bank_name: str = None, branch_name: str = None, ifsc_code: str = None,
                              transaction_reference: str = None, remarks: str = None):
        """Create advance payment - auto DRAFT for UPI/online modes"""
        from modules.account_module.models.payment_entity import Payment, PaymentDetail
        from modules.admin_module.models.currency import Currency
        
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                # Check if payment number already exists
                existing = session.query(Payment).filter(
                    Payment.tenant_id == tenant_id,
                    Payment.payment_number == payment_number,
                    Payment.is_deleted == False
                ).first()
                
                if existing:
                    raise ValueError(f"Payment number '{payment_number}' already exists")
                
                # Auto-determine status and payment type based on payment mode and party type
                online_modes = ['UPI', 'ONLINE', 'CARD', 'WALLET', 'NEFT', 'RTGS', 'IMPS']
                status = 'DRAFT' if payment_mode in online_modes else 'POSTED'
                
                # Determine payment type based on party type
                if party_type in ['CUSTOMER', 'PATIENT']:
                    payment_type = 'RECEIPT'
                elif party_type in ['SUPPLIER', 'EMPLOYEE']:
                    payment_type = 'PAYMENT'
                else:
                    payment_type = 'RECEIPT'  # Default
                
                # Get base currency from tenant settings
                base_currency = session.query(Currency).join(
                    TenantSetting, 
                    TenantSetting.value == Currency.code
                ).filter(
                    TenantSetting.tenant_id == tenant_id,
                    TenantSetting.setting.ilike("base_currency"),
                    TenantSetting.value_type.ilike("CURRENCY")
                ).first()

                
                if not base_currency:
                    raise ValueError("No active currency found")
                
                payment = Payment(
                    tenant_id=tenant_id,
                    payment_number=payment_number,
                    payment_date=datetime.now(),
                    payment_type=payment_type,
                    party_type=party_type,
                    party_id=party_id,
                    party_name=party_name,
                    party_phone=party_phone,
                    base_currency_id=base_currency.id,
                    exchange_rate=Decimal(1),
                    total_amount_base=amount,
                    advance_amount_base=amount,
                    allocated_amount_base=Decimal(0),
                    unallocated_amount_base=amount,
                    status=status,
                    remarks=remarks or f"Advance payment - {payment_mode}",
                    created_by=username,
                    updated_by=username
                )
                
                session.add(payment)
                session.flush()
                
                detail = PaymentDetail(
                    tenant_id=tenant_id,
                    payment_id=payment.id,
                    line_no=1,
                    payment_mode=payment_mode,
                    instrument_number=instrument_number,
                    instrument_date=instrument_date,
                    bank_name=bank_name,
                    branch_name=branch_name,
                    ifsc_code=ifsc_code,
                    transaction_reference=transaction_reference,
                    amount_base=amount,
                    description=f"Advance payment - {payment_mode}",
                    created_by=username,
                    updated_by=username
                )
                session.add(detail)
                
                # Create voucher only for POSTED (CASH/CHEQUE/BANK)
                if status == 'POSTED':
                    voucher = self._create_advance_payment_voucher(session, tenant_id, username, payment, payment_mode, amount)
                    payment.voucher_id = voucher.id
                
                session.commit()
                session.refresh(payment)
                
                return self._payment_to_dict(payment, include_details=True)
            except Exception as e:
                session.rollback()
                raise
    
    def _create_advance_payment_voucher(self, session, tenant_id, username, payment, payment_mode, amount):
        """Create voucher for advance payment"""
        voucher_type = session.query(VoucherType).filter(
            VoucherType.tenant_id == tenant_id,
            VoucherType.code == 'RECEIPT',
            VoucherType.is_active == True
        ).first()
        
        if not voucher_type:
            raise ValueError("RECEIPT voucher type not configured")
        
        voucher = Voucher(
            tenant_id=tenant_id,
            voucher_number=f"REC-{payment.payment_number}",
            voucher_type_id=voucher_type.id,
            voucher_date=payment.payment_date,
            base_currency_id=payment.base_currency_id,
            exchange_rate=payment.exchange_rate,
            base_total_amount=amount,
            base_total_debit=amount,
            base_total_credit=amount,
            reference_type='ADVANCE_PAYMENT',
            reference_id=payment.id,
            reference_number=payment.payment_number,
            narration=f"Advance payment - {payment.remarks or ''}",
            is_posted=True,
            created_by=username,
            updated_by=username
        )
        
        session.add(voucher)
        session.flush()
        
        payment_account_id = self._get_configured_account(session, tenant_id, 'CASH' if payment_mode == 'CASH' else 'BANK')
        advance_account_id = self._get_configured_account(session, tenant_id, 'CUSTOMER_ADVANCE')
        
        session.add(VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=1,
            account_id=payment_account_id,
            description=f"Advance received - {payment_mode}",
            debit_base=amount,
            credit_base=Decimal(0),
            created_by=username,
            updated_by=username
        ))
        
        session.add(VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=2,
            account_id=advance_account_id,
            description=f"Customer advance liability",
            debit_base=Decimal(0),
            credit_base=amount,
            created_by=username,
            updated_by=username
        ))
        
        return voucher
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def create_invoice_payment_simple(self, payment_number: str, invoice_id: int, invoice_type: str, 
                                     party_name: str, party_phone: str, amount: Decimal, payment_mode: str = 'CASH',
                                     instrument_number: str = None, instrument_date: date = None,
                                     bank_name: str = None, branch_name: str = None, ifsc_code: str = None,
                                     transaction_reference: str = None, remarks: str = None):
        """Create payment against invoice with auto status determination"""
        from modules.account_module.models.payment_entity import Payment, PaymentDetail, PaymentAllocation
        from modules.admin_module.models.currency import Currency
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            # Check if payment number already exists
            existing = session.query(Payment).filter(
                Payment.tenant_id == tenant_id,
                Payment.payment_number == payment_number,
                Payment.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Payment number '{payment_number}' already exists")
            
            # Get invoice and validate based on invoice_type
            if invoice_type == 'SALES':
                from modules.inventory_module.models.sales_invoice_entity import SalesInvoice
                invoice = session.query(SalesInvoice).filter(
                    SalesInvoice.id == invoice_id,
                    SalesInvoice.tenant_id == tenant_id,
                    SalesInvoice.is_deleted == False
                ).first()
                payment_type = 'RECEIPT'
                party_type = 'CUSTOMER'
                party_id_field = 'customer_id'
            elif invoice_type == 'PURCHASE':
                from modules.inventory_module.models.purchase_invoice_entity import PurchaseInvoice
                invoice = session.query(PurchaseInvoice).filter(
                    PurchaseInvoice.id == invoice_id,
                    PurchaseInvoice.tenant_id == tenant_id,
                    PurchaseInvoice.is_deleted == False
                ).first()
                payment_type = 'PAYMENT'
                party_type = 'SUPPLIER'
                party_id_field = 'supplier_id'
            elif invoice_type == 'TEST':
                from modules.health_module.models.test_invoice_entity import TestInvoice
                invoice = session.query(TestInvoice).filter(
                    TestInvoice.id == invoice_id,
                    TestInvoice.tenant_id == tenant_id,
                    TestInvoice.is_deleted == False
                ).first()
                payment_type = 'RECEIPT'
                party_type = 'PATIENT'
                party_id_field = 'patient_id'
            elif invoice_type == 'CLINIC':
                from modules.health_module.models.appointment_invoice_entity import AppointmentInvoice
                invoice = session.query(AppointmentInvoice).filter(
                    AppointmentInvoice.id == invoice_id,
                    AppointmentInvoice.tenant_id == tenant_id,
                    AppointmentInvoice.is_deleted == False
                ).first()
                payment_type = 'RECEIPT'
                party_type = 'PATIENT'
                party_id_field = 'patient_id'
            else:
                raise ValueError(f"Invalid invoice_type: {invoice_type}")
            
            if not invoice:
                raise ValueError(f"{invoice_type} invoice not found")
            
            # Calculate balance
            current_paid = invoice.paid_amount or Decimal(0)
            total_amount = invoice.final_amount if hasattr(invoice, 'final_amount') else invoice.total_amount_base
            current_balance = total_amount - current_paid
            
            if amount > current_balance:
                raise ValueError(f"Payment amount {amount} exceeds invoice balance {current_balance}")
            
            # Auto-determine status
            online_modes = ['UPI', 'ONLINE', 'CARD', 'WALLET', 'NEFT', 'RTGS', 'IMPS']
            status = 'DRAFT' if payment_mode in online_modes else 'POSTED'
            
            # Get base currency from tenant settings
            currency_code=TenantSettingsService().get_tenant_settings(tenant_id).get("base_currency",None)
            if not currency_code:
                raise ValueError("No default currency found")
            base_currency = CurrencyService.get_currency_by_code(currency_code)
            if not base_currency:
                raise ValueError("No active currency found")
            
            # Create payment
            payment = Payment(
                tenant_id=tenant_id,
                payment_number=payment_number,
                payment_date=datetime.now(),
                payment_type=payment_type,
                party_type=party_type,
                party_id=getattr(invoice, party_id_field),
                party_name=party_name,
                party_phone=party_phone,
                base_currency_id=base_currency.id,
                exchange_rate=Decimal(1),
                total_amount_base=amount,
                allocated_amount_base=amount,
                unallocated_amount_base=Decimal(0),
                status=status,
                remarks=remarks or f"Payment for {invoice_type} invoice {invoice.invoice_number}",
                created_by=username,
                updated_by=username
            )
            
            session.add(payment)
            session.flush()
            
            # Create payment detail
            detail = PaymentDetail(
                tenant_id=tenant_id,
                payment_id=payment.id,
                line_no=1,
                payment_mode=payment_mode,
                instrument_number=instrument_number,
                instrument_date=instrument_date,
                bank_name=bank_name,
                branch_name=branch_name,
                ifsc_code=ifsc_code,
                transaction_reference=transaction_reference,
                amount_base=amount,
                description=f"Payment - {payment_mode}",
                created_by=username,
                updated_by=username
            )
            session.add(detail)
            
            # Create allocation
            allocation = PaymentAllocation(
                tenant_id=tenant_id,
                payment_id=payment.id,
                document_type=invoice_type,
                document_id=invoice_id,
                document_number=invoice.invoice_number,
                allocated_amount_base=amount,
                allocation_date=datetime.now(),
                remarks=f"Payment against invoice {invoice.invoice_number}",
                created_by=username,
                updated_by=username
            )
            session.add(allocation)
            
            # Update invoice and create voucher only if POSTED
            if status == 'POSTED':
                # Update invoice amounts
                new_paid_amount = current_paid + amount
                new_balance = total_amount - new_paid_amount
                
                invoice.paid_amount = new_paid_amount
                
                # Update payment status based on amounts
                if new_paid_amount == 0:
                    invoice.payment_status = 'UNPAID'
                elif new_paid_amount < total_amount:
                    invoice.payment_status = 'PARTIAL'
                elif new_paid_amount == total_amount:
                    invoice.payment_status = 'PAID'
                else:
                    invoice.payment_status = 'OVERPAID'
                
                invoice.updated_by = username
                invoice.updated_at = datetime.now()
                
                # Create voucher
                voucher = self._create_invoice_payment_voucher_simple(
                    session, tenant_id, username, payment, invoice, invoice_type, payment_mode, amount
                )
                payment.voucher_id = voucher.id
            
            session.commit()
            session.refresh(payment)
            
            return self._payment_to_dict(payment, include_details=True)
    
    def _create_invoice_payment_voucher_simple(self, session, tenant_id, username, payment, invoice, invoice_type, payment_mode, amount):
        """Create voucher for invoice payment"""
        voucher_type_code = 'RECEIPT' if invoice_type in ['SALES', 'TEST'] else 'PAYMENT'
        voucher_type = session.query(VoucherType).filter(
            VoucherType.tenant_id == tenant_id,
            VoucherType.code == voucher_type_code,
            VoucherType.is_active == True
        ).first()
        
        if not voucher_type:
            raise ValueError(f"{voucher_type_code} voucher type not configured")
        
        voucher = Voucher(
            tenant_id=tenant_id,
            voucher_number=f"{voucher_type_code[:3]}-{payment.payment_number}",
            voucher_type_id=voucher_type.id,
            voucher_date=payment.payment_date,
            base_currency_id=payment.base_currency_id,
            exchange_rate=payment.exchange_rate,
            base_total_amount=amount,
            base_total_debit=amount,
            base_total_credit=amount,
            reference_type='INVOICE_PAYMENT',
            reference_id=payment.id,
            reference_number=payment.payment_number,
            narration=f"Payment for invoice {invoice.invoice_number}",
            is_posted=True,
            created_by=username,
            updated_by=username
        )
        
        session.add(voucher)
        session.flush()
        
        payment_account_id = self._get_configured_account(session, tenant_id, 'CASH' if payment_mode == 'CASH' else 'BANK')
        
        if invoice_type == 'TEST':
            # For TEST invoices, use AR account directly (Patient receivable)
            ar_account = session.query(AccountMaster).filter(
                AccountMaster.code == '1100-AR',
                AccountMaster.tenant_id == tenant_id
            ).first()
            
            if not ar_account:
                raise ValueError("AR account not found")
            
            party_account_id = ar_account.id
        else:
            party_account_id = self._get_or_create_party_account(session, tenant_id, payment.party_type, payment.party_id, username)
        
        if invoice_type in ['SALES', 'TEST']:
            # Debit: Cash/Bank, Credit: Customer/Patient
            session.add(VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=1,
                account_id=payment_account_id,
                description=f"Payment received - {payment_mode}",
                debit_base=amount,
                credit_base=Decimal(0),
                created_by=username,
                updated_by=username
            ))
            
            session.add(VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=2,
                account_id=party_account_id,
                description=f"{'Patient' if invoice_type == 'TEST' else 'Customer'} payment - {invoice.invoice_number}",
                debit_base=Decimal(0),
                credit_base=amount,
                created_by=username,
                updated_by=username
            ))
        else:
            # Debit: Supplier, Credit: Cash/Bank
            session.add(VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=1,
                account_id=party_account_id,
                description=f"Supplier payment - {invoice.invoice_number}",
                debit_base=amount,
                credit_base=Decimal(0),
                created_by=username,
                updated_by=username
            ))
            
            session.add(VoucherLine(
                tenant_id=tenant_id,
                voucher_id=voucher.id,
                line_no=2,
                account_id=payment_account_id,
                description=f"Payment made - {payment_mode}",
                debit_base=Decimal(0),
                credit_base=amount,
                created_by=username,
                updated_by=username
            ))
        
        return voucher

    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def confirm_gateway_payment(self, payment_id: int, transaction_reference: str, gateway_transaction_id: str = None, 
                               gateway_status: str = 'SUCCESS', gateway_fee_base: Decimal = None, gateway_response: str = None):
        """Update DRAFT payment with gateway response - POSTED on SUCCESS, stays DRAFT on FAILED"""
        from modules.account_module.models.payment_entity import Payment, PaymentDetail, PaymentAllocation
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            payment = session.query(Payment).filter(
                Payment.id == payment_id,
                Payment.tenant_id == tenant_id,
                Payment.is_deleted == False
            ).first()
            
            if not payment:
                raise ValueError("Payment not found")
            
            if payment.status != 'DRAFT':
                raise ValueError(f"Cannot confirm payment with status {payment.status}. Only DRAFT payments can be confirmed")
            
            # Update payment detail with gateway info
            detail = session.query(PaymentDetail).filter(
                PaymentDetail.payment_id == payment_id
            ).first()
            
            if detail:
                detail.transaction_reference = transaction_reference
                detail.payment_gateway = gateway_transaction_id.split('-')[0] if gateway_transaction_id else 'UPI'
                detail.gateway_transaction_id = gateway_transaction_id
                detail.gateway_status = gateway_status
                detail.gateway_fee_base = gateway_fee_base or Decimal(0)
                detail.gateway_response = gateway_response
                detail.updated_by = username
            
            # Update payment reference
            payment.reference_number = transaction_reference
            payment.updated_by = username
            
            # Only post payment if gateway status is SUCCESS
            if gateway_status == 'SUCCESS':
                payment.status = 'POSTED'
                
                # Check if this is advance or invoice payment
                allocation = session.query(PaymentAllocation).filter(
                    PaymentAllocation.payment_id == payment_id
                ).first()
                
                if allocation:
                    # Invoice payment - update invoice
                    invoice_type = 'SALES' if payment.payment_type == 'RECEIPT' else 'PURCHASE'
                    
                    # Check if it's a test invoice by checking party_type
                    if payment.party_type == 'PATIENT':
                        invoice_type = 'TEST'
                        from modules.health_module.models.test_invoice_entity import TestInvoice
                        invoice = session.query(TestInvoice).filter(
                            TestInvoice.id == allocation.document_id,
                            TestInvoice.tenant_id == tenant_id
                        ).first()
                    elif invoice_type == 'SALES':
                        from modules.inventory_module.models.sales_invoice_entity import SalesInvoice
                        invoice = session.query(SalesInvoice).filter(
                            SalesInvoice.id == allocation.document_id,
                            SalesInvoice.tenant_id == tenant_id
                        ).first()
                    else:
                        from modules.inventory_module.models.purchase_invoice_entity import PurchaseInvoice
                        invoice = session.query(PurchaseInvoice).filter(
                            PurchaseInvoice.id == allocation.document_id,
                            PurchaseInvoice.tenant_id == tenant_id
                        ).first()
                    
                    if invoice:
                        # Update invoice amounts
                        current_paid = invoice.paid_amount or Decimal(0)
                        total_amount = invoice.final_amount if hasattr(invoice, 'final_amount') else invoice.total_amount_base
                        new_paid_amount = current_paid + payment.total_amount_base
                        
                        invoice.paid_amount = new_paid_amount
                        
                        # Update payment status
                        if new_paid_amount == 0:
                            invoice.payment_status = 'UNPAID'
                        elif new_paid_amount < total_amount:
                            invoice.payment_status = 'PARTIAL'
                        elif new_paid_amount == total_amount:
                            invoice.payment_status = 'PAID'
                        else:
                            invoice.payment_status = 'OVERPAID'
                        
                        invoice.updated_by = username
                        invoice.updated_at = datetime.now()
                        
                        # Create voucher for invoice payment
                        voucher = self._create_invoice_payment_voucher_simple(
                            session, tenant_id, username, payment, invoice, invoice_type, 
                            detail.payment_mode if detail else 'UPI', payment.total_amount_base
                        )
                        payment.voucher_id = voucher.id
                else:
                    # Advance payment - create voucher
                    voucher = self._create_advance_payment_voucher(
                        session, tenant_id, username, payment, 
                        detail.payment_mode if detail else 'UPI', payment.total_amount_base
                    )
                    payment.voucher_id = voucher.id
            # If FAILED, payment stays DRAFT with gateway info updated
            
            session.commit()
            session.refresh(payment)
            
            return self._payment_to_dict(payment, include_details=True)

    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def get_payment_allocations(self, payment_id: int):
        """Get all allocations for a payment"""
        from modules.account_module.models.payment_entity import PaymentAllocation
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            allocations = session.query(PaymentAllocation).filter(
                PaymentAllocation.payment_id == payment_id,
                PaymentAllocation.tenant_id == tenant_id,
                PaymentAllocation.is_deleted == False
            ).all()
            
            return [self._allocation_to_dict(a) for a in allocations]
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def get_document_payments(self, document_type: str, document_id: int):
        """Get all payments for a document"""
        from modules.account_module.models.payment_entity import PaymentAllocation
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            allocations = session.query(PaymentAllocation).filter(
                PaymentAllocation.document_type == document_type.upper(),
                PaymentAllocation.document_id == document_id,
                PaymentAllocation.tenant_id == tenant_id,
                PaymentAllocation.is_deleted == False
            ).all()
            
            return [self._allocation_to_dict(a) for a in allocations]
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def allocate_payment_to_invoices(self, payment_id: int, allocation_data: dict):
        """Allocate payment to multiple invoices with validation"""
        from modules.account_module.models.payment_entity import Payment, PaymentAllocation
        
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                # Get payment
                payment = session.query(Payment).filter(
                    Payment.id == payment_id,
                    Payment.tenant_id == tenant_id,
                    Payment.is_deleted == False
                ).first()
                
                if not payment:
                    raise ValueError("Payment not found")
                
                if payment.status not in ['POSTED', 'RECONCILED']:
                    raise ValueError(f"Cannot allocate payment with status {payment.status}. Only POSTED or RECONCILED payments can be allocated")
                
                if payment.unallocated_amount_base <= 0:
                    raise ValueError("Payment has no unallocated amount")
                
                allocations_list = allocation_data.get('allocations', [])
                
                # Validate total allocation amount
                total_allocation = sum(Decimal(str(item['allocated_amount'])) for item in allocations_list)
                
                if total_allocation > payment.unallocated_amount_base:
                    raise ValueError(
                        f"Total allocation amount {total_allocation} exceeds unallocated amount {payment.unallocated_amount_base}"
                    )
                
                created_allocations = []
                
                # Process each allocation
                for item in allocations_list:
                    doc_type = item['document_type']
                    doc_id = item['document_id']
                    allocated_amt = Decimal(str(item['allocated_amount']))
                    remarks = item.get('remarks')
                    
                    # Check for existing allocation
                    existing = session.query(PaymentAllocation).filter(
                        PaymentAllocation.payment_id == payment_id,
                        PaymentAllocation.document_type == doc_type,
                        PaymentAllocation.document_id == doc_id,
                        PaymentAllocation.tenant_id == tenant_id,
                        PaymentAllocation.is_deleted == False
                    ).first()
                    
                    if existing:
                        raise ValueError(f"Payment already allocated to {doc_type} ID {doc_id}")
                    
                    # Get invoice and validate
                    invoice = self._get_invoice_by_type(session, tenant_id, doc_type, doc_id)
                    
                    if not invoice:
                        raise ValueError(f"{doc_type} invoice with ID {doc_id} not found")
                    
                    # Calculate invoice balance
                    total_amt = invoice.final_amount if hasattr(invoice, 'final_amount') else invoice.total_amount_base
                    paid_amt = invoice.paid_amount or Decimal(0)
                    balance = total_amt - paid_amt
                    
                    if allocated_amt > balance:
                        raise ValueError(
                            f"Allocation amount {allocated_amt} exceeds invoice balance {balance} for {doc_type} {invoice.invoice_number}"
                        )
                    
                    # Create allocation
                    allocation = PaymentAllocation(
                        tenant_id=tenant_id,
                        payment_id=payment_id,
                        document_type=doc_type,
                        document_id=doc_id,
                        document_number=invoice.invoice_number,
                        allocated_amount_base=allocated_amt,
                        allocation_date=datetime.now(),
                        remarks=remarks,
                        created_by=username,
                        updated_by=username
                    )
                    session.add(allocation)
                    session.flush()
                    
                    # Update invoice payment status
                    new_paid = paid_amt + allocated_amt
                    invoice.paid_amount = new_paid
                    
                    if new_paid >= total_amt:
                        invoice.payment_status = 'PAID'
                    elif new_paid > 0:
                        invoice.payment_status = 'PARTIAL'
                    else:
                        invoice.payment_status = 'UNPAID'
                    
                    invoice.updated_by = username
                    invoice.updated_at = datetime.now()
                    
                    created_allocations.append(self._allocation_to_dict(allocation))
                
                # Update payment amounts
                payment.allocated_amount_base = (payment.allocated_amount_base or Decimal(0)) + total_allocation
                payment.unallocated_amount_base = payment.unallocated_amount_base - total_allocation
                payment.updated_by = username
                payment.updated_at = datetime.now()
                
                session.commit()
                
                return {
                    'payment_id': payment.id,
                    'payment_number': payment.payment_number,
                    'total_allocated': float(total_allocation),
                    'remaining_unallocated': float(payment.unallocated_amount_base),
                    'allocations': created_allocations
                }
                
            except Exception as e:
                session.rollback()
                raise
    
    def _get_invoice_by_type(self, session, tenant_id, doc_type, doc_id):
        """Get invoice based on document type"""
        if doc_type == 'TEST':
            from modules.health_module.models.test_invoice_entity import TestInvoice
            return session.query(TestInvoice).filter(
                TestInvoice.id == doc_id,
                TestInvoice.tenant_id == tenant_id,
                TestInvoice.is_deleted == False
            ).first()
        elif doc_type in ['SALES', 'INVOICE']:
            from modules.inventory_module.models.sales_invoice_entity import SalesInvoice
            return session.query(SalesInvoice).filter(
                SalesInvoice.id == doc_id,
                SalesInvoice.tenant_id == tenant_id,
                SalesInvoice.is_deleted == False
            ).first()
        elif doc_type == 'PURCHASE':
            from modules.inventory_module.models.purchase_invoice_entity import PurchaseInvoice
            return session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == doc_id,
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.is_deleted == False
            ).first()
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")
