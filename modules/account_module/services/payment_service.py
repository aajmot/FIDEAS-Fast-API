from core.database.connection import db_manager
from modules.account_module.models.entities import *
from modules.account_module.services.account_service import AccountService
from modules.account_module.services.audit_service import AuditService
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from sqlalchemy import or_
from datetime import datetime
from decimal import Decimal

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
            AccountMaster.code == 'AR001',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        sales_account = session.query(AccountMaster).filter(
            AccountMaster.code == 'SAL001',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        cogs_account = session.query(AccountMaster).filter(
            AccountMaster.code == 'COGS001',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        inventory_account = session.query(AccountMaster).filter(
            AccountMaster.code == 'INV001',
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
            AccountMaster.code == 'INV001',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        ap_account = session.query(AccountMaster).filter(
            AccountMaster.code == 'AP001',
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
            AccountMaster.code == 'INV001',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        expense_account = session.query(AccountMaster).filter(
            AccountMaster.code == 'EXP001',
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
            AccountMaster.code == 'AR001',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        sales_account = session.query(AccountMaster).filter(
            AccountMaster.code == 'SAL001',
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
            AccountMaster.code == 'INV001',
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        ap_account = session.query(AccountMaster).filter(
            AccountMaster.code == 'AP001',
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
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def get_all_payments(self, page=1, page_size=100, search=None, payment_type=None, 
                        party_type=None, status=None, date_from=None, date_to=None,
                        is_reconciled=None):
        """Get all payments with pagination and filters"""
        from modules.account_module.models.payment_entity import Payment
        import math
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(Payment).filter(
                Payment.tenant_id == tenant_id,
                Payment.is_deleted == False
            )
            
            # Apply filters
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        Payment.payment_number.ilike(search_pattern),
                        Payment.reference_number.ilike(search_pattern),
                        Payment.remarks.ilike(search_pattern)
                    )
                )
            
            if payment_type:
                query = query.filter(Payment.payment_type == payment_type)
            
            if party_type:
                query = query.filter(Payment.party_type == party_type)
            
            if status:
                query = query.filter(Payment.status == status)
            
            if date_from:
                query = query.filter(Payment.payment_date >= date_from)
            
            if date_to:
                query = query.filter(Payment.payment_date <= date_to)
            
            if is_reconciled is not None:
                query = query.filter(Payment.is_reconciled == is_reconciled)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            query = query.order_by(Payment.payment_date.desc(), Payment.id.desc())
            offset = (page - 1) * page_size
            payments = query.offset(offset).limit(page_size).all()
            
            return {
                'total': total,
                'page': page,
                'per_page': page_size,
                'total_pages': math.ceil(total / page_size) if total > 0 else 0,
                'data': [self._payment_to_dict(p, include_details=False) for p in payments]
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
    
    def _payment_to_dict(self, payment, include_details=True):
        """Convert payment entity to dictionary"""
        result = {
            'id': payment.id,
            'payment_number': payment.payment_number,
            'payment_date': payment.payment_date,
            'payment_type': payment.payment_type,
            'party_type': payment.party_type,
            'party_id': payment.party_id,
            'base_currency_id': payment.base_currency_id,
            'foreign_currency_id': payment.foreign_currency_id,
            'exchange_rate': payment.exchange_rate,
            'total_amount_base': payment.total_amount_base,
            'total_amount_foreign': payment.total_amount_foreign,
            'tds_amount_base': payment.tds_amount_base,
            'advance_amount_base': payment.advance_amount_base,
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
        
        if include_details:
            result['details'] = [self._detail_to_dict(detail) for detail in payment.payment_details]
        else:
            result['details'] = []
        
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
            'description': detail.description
        }