from core.database.connection import db_manager
from modules.account_module.models.entities import *
from modules.account_module.services.account_service import AccountService
from modules.account_module.services.audit_service import AuditService
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
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
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def record_payment(self, payment_data):
        """Record cash/bank payment (reduces AP or other payables)"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            # Get cash/bank account
            cash_account = session.query(AccountMaster).filter(
                AccountMaster.id == payment_data['account_id'],
                AccountMaster.tenant_id == tenant_id
            ).first()
            
            # Get payable account (AP or other)
            payable_account = session.query(AccountMaster).filter(
                AccountMaster.code == 'AP001',
                AccountMaster.tenant_id == tenant_id
            ).first()
            
            if not cash_account or not payable_account:
                raise ValueError("Required accounts not found")
            
            # Get voucher type
            voucher_type = session.query(VoucherType).filter(
                VoucherType.code == 'PAY',
                VoucherType.tenant_id == tenant_id
            ).first()
            
            if not voucher_type:
                voucher_type = session.query(VoucherType).filter(
                    VoucherType.code == 'JV',
                    VoucherType.tenant_id == tenant_id
                ).first()
            
            if not voucher_type:
                raise ValueError("Payment voucher type not found. Please initialize default voucher types.")
            
            # Create payment record
            payment = Payment(
                payment_number=payment_data['payment_number'],
                payment_date=payment_data['payment_date'],
                payment_type=payment_data['payment_type'],
                payment_mode='PAID',
                reference_type=payment_data.get('reference_type', 'GENERAL'),
                reference_id=payment_data.get('reference_id', 0),
                reference_number=payment_data.get('reference_number', ''),
                amount=payment_data['amount'],
                account_id=cash_account.id,
                remarks=payment_data.get('remarks', ''),
                tenant_id=tenant_id,
                created_by=username
            )
            session.add(payment)
            session.flush()
            
            # Create voucher
            voucher = Voucher(
                voucher_number=payment_data['payment_number'],
                voucher_type_id=voucher_type.id,
                voucher_date=payment_data['payment_date'],
                reference_type='PAYMENT',
                reference_id=payment.id,
                reference_number=payment_data['payment_number'],
                narration=payment_data.get('remarks', 'Payment made'),
                total_amount=payment_data['amount'],
                is_posted=True,
                tenant_id=tenant_id,
                created_by=username
            )
            session.add(voucher)
            session.flush()
            
            payment.voucher_id = voucher.id
            
            # Create journal
            journal = Journal(
                voucher_id=voucher.id,
                journal_date=payment_data['payment_date'],
                total_debit=payment_data['amount'],
                total_credit=payment_data['amount'],
                tenant_id=tenant_id
            )
            session.add(journal)
            session.flush()
            
            # Journal details - Debit AP, Credit Cash/Bank
            journal_details = [
                JournalDetail(
                    journal_id=journal.id,
                    account_id=payable_account.id,
                    debit_amount=payment_data['amount'],
                    credit_amount=0,
                    narration=f"Payment - {payment_data['payment_number']}",
                    tenant_id=tenant_id
                ),
                JournalDetail(
                    journal_id=journal.id,
                    account_id=cash_account.id,
                    debit_amount=0,
                    credit_amount=payment_data['amount'],
                    narration=f"Payment - {payment_data['payment_number']}",
                    tenant_id=tenant_id
                )
            ]
            
            for detail in journal_details:
                session.add(detail)
            
            # Ledger entries
            ledger_entries = [
                Ledger(
                    account_id=payable_account.id,
                    voucher_id=voucher.id,
                    transaction_date=payment_data['payment_date'],
                    debit_amount=payment_data['amount'],
                    credit_amount=0,
                    balance=(payable_account.current_balance or Decimal('0')) - Decimal(str(payment_data['amount'])),
                    narration=f"Payment - {payment_data['payment_number']}",
                    tenant_id=tenant_id
                ),
                Ledger(
                    account_id=cash_account.id,
                    voucher_id=voucher.id,
                    transaction_date=payment_data['payment_date'],
                    debit_amount=0,
                    credit_amount=payment_data['amount'],
                    balance=(cash_account.current_balance or Decimal('0')) - Decimal(str(payment_data['amount'])),
                    narration=f"Payment - {payment_data['payment_number']}",
                    tenant_id=tenant_id
                )
            ]
            
            for ledger in ledger_entries:
                session.add(ledger)
            
            # Update balances
            self.account_service.update_account_balance_in_session(session, payable_account.id, payment_data['amount'], 'DEBIT')
            self.account_service.update_account_balance_in_session(session, cash_account.id, payment_data['amount'], 'CREDIT')
            
            # Log audit trail
            AuditService.log_action(
                session, 'PAYMENT', payment.id, 'CREATE',
                new_value={'payment_number': payment.payment_number, 'amount': float(payment.amount)}
            )
            
            session.commit()
            return payment
    
    @ExceptionMiddleware.handle_exceptions("PaymentService")
    def record_receipt(self, receipt_data):
        """Record cash/bank receipt (reduces AR or other receivables)"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            # Get cash/bank account
            cash_account = session.query(AccountMaster).filter(
                AccountMaster.id == receipt_data['account_id'],
                AccountMaster.tenant_id == tenant_id
            ).first()
            
            # Get receivable account (AR or other)
            receivable_account = session.query(AccountMaster).filter(
                AccountMaster.code == 'AR001',
                AccountMaster.tenant_id == tenant_id
            ).first()
            
            if not cash_account or not receivable_account:
                raise ValueError("Required accounts not found")
            
            # Get voucher type
            voucher_type = session.query(VoucherType).filter(
                VoucherType.code == 'REC',
                VoucherType.tenant_id == tenant_id
            ).first()
            
            if not voucher_type:
                voucher_type = session.query(VoucherType).filter(
                    VoucherType.code == 'JV',
                    VoucherType.tenant_id == tenant_id
                ).first()
            
            if not voucher_type:
                raise ValueError("Receipt voucher type not found. Please initialize default voucher types.")
            
            # Create payment record
            receipt = Payment(
                payment_number=receipt_data['payment_number'],
                payment_date=receipt_data['payment_date'],
                payment_type=receipt_data['payment_type'],
                payment_mode='RECEIVED',
                reference_type=receipt_data.get('reference_type', 'SALES'),
                reference_id=receipt_data.get('reference_id', 0),
                reference_number=receipt_data.get('reference_number', ''),
                amount=receipt_data['amount'],
                account_id=cash_account.id,
                remarks=receipt_data.get('remarks', ''),
                tenant_id=tenant_id,
                created_by=username
            )
            session.add(receipt)
            session.flush()
            
            # Create voucher
            voucher = Voucher(
                voucher_number=receipt_data['payment_number'],
                voucher_type_id=voucher_type.id,
                voucher_date=receipt_data['payment_date'],
                reference_type='RECEIPT',
                reference_id=receipt.id,
                reference_number=receipt_data['payment_number'],
                narration=receipt_data.get('remarks', 'Receipt received'),
                total_amount=receipt_data['amount'],
                is_posted=True,
                tenant_id=tenant_id,
                created_by=username
            )
            session.add(voucher)
            session.flush()
            
            receipt.voucher_id = voucher.id
            
            # Create journal
            journal = Journal(
                voucher_id=voucher.id,
                journal_date=receipt_data['payment_date'],
                total_debit=receipt_data['amount'],
                total_credit=receipt_data['amount'],
                tenant_id=tenant_id
            )
            session.add(journal)
            session.flush()
            
            # Journal details - Debit Cash/Bank, Credit AR
            journal_details = [
                JournalDetail(
                    journal_id=journal.id,
                    account_id=cash_account.id,
                    debit_amount=receipt_data['amount'],
                    credit_amount=0,
                    narration=f"Receipt - {receipt_data['payment_number']}",
                    tenant_id=tenant_id
                ),
                JournalDetail(
                    journal_id=journal.id,
                    account_id=receivable_account.id,
                    debit_amount=0,
                    credit_amount=receipt_data['amount'],
                    narration=f"Receipt - {receipt_data['payment_number']}",
                    tenant_id=tenant_id
                )
            ]
            
            for detail in journal_details:
                session.add(detail)
            
            # Ledger entries
            ledger_entries = [
                Ledger(
                    account_id=cash_account.id,
                    voucher_id=voucher.id,
                    transaction_date=receipt_data['payment_date'],
                    debit_amount=receipt_data['amount'],
                    credit_amount=0,
                    balance=(cash_account.current_balance or Decimal('0')) + Decimal(str(receipt_data['amount'])),
                    narration=f"Receipt - {receipt_data['payment_number']}",
                    tenant_id=tenant_id
                ),
                Ledger(
                    account_id=receivable_account.id,
                    voucher_id=voucher.id,
                    transaction_date=receipt_data['payment_date'],
                    debit_amount=0,
                    credit_amount=receipt_data['amount'],
                    balance=(receivable_account.current_balance or Decimal('0')) - Decimal(str(receipt_data['amount'])),
                    narration=f"Receipt - {receipt_data['payment_number']}",
                    tenant_id=tenant_id
                )
            ]
            
            for ledger in ledger_entries:
                session.add(ledger)
            
            # Update balances
            self.account_service.update_account_balance_in_session(session, cash_account.id, receipt_data['amount'], 'DEBIT')
            self.account_service.update_account_balance_in_session(session, receivable_account.id, receipt_data['amount'], 'CREDIT')
            
            # Log audit trail
            AuditService.log_action(
                session, 'PAYMENT', receipt.id, 'CREATE',
                new_value={'payment_number': receipt.payment_number, 'amount': float(receipt.amount)}
            )
            
            session.commit()
            return receipt