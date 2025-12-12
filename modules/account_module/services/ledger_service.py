from core.database.connection import db_manager
from modules.account_module.models.ledger_entity import Ledger
from modules.account_module.models.entities import AccountMaster, Voucher, VoucherLine
from core.shared.utils.logger import logger
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from sqlalchemy import func, and_, or_
from datetime import datetime
from decimal import Decimal

class LedgerService:
    def __init__(self):
        self.logger_name = "LedgerService"
    
    @ExceptionMiddleware.handle_exceptions("LedgerService")
    def create_from_voucher(self, voucher_id: int, session=None):
        """Create ledger entries from voucher lines"""
        should_close = session is None
        if session is None:
            session = db_manager.get_session().__enter__()
        
        try:
            tenant_id = session_manager.get_current_tenant_id()
            
            voucher = session.query(Voucher).filter(
                Voucher.id == voucher_id,
                Voucher.tenant_id == tenant_id
            ).first()
            
            if not voucher:
                raise ValueError("Voucher not found")
            
            voucher_lines = session.query(VoucherLine).filter(
                VoucherLine.voucher_id == voucher_id,
                VoucherLine.tenant_id == tenant_id
            ).all()
            
            ledger_entries = []
            for line in voucher_lines:
                ledger = Ledger(
                    tenant_id=tenant_id,
                    account_id=line.account_id,
                    voucher_id=voucher_id,
                    voucher_line_id=line.id,
                    transaction_date=voucher.voucher_date,
                    posting_date=datetime.utcnow(),
                    debit_amount=line.debit_base or 0,
                    credit_amount=line.credit_base or 0,
                    currency_id=voucher.foreign_currency_id,
                    exchange_rate=voucher.exchange_rate or 1,
                    debit_foreign=line.debit_foreign,
                    credit_foreign=line.credit_foreign,
                    narration=line.description or voucher.narration,
                    reference_type=voucher.reference_type,
                    reference_id=voucher.reference_id,
                    reference_number=voucher.reference_number,
                    is_posted=voucher.is_posted,
                    created_by=session_manager.get_current_username()
                )
                session.add(ledger)
                ledger_entries.append(ledger)
            
            session.flush()
            
            # Update balances for affected accounts
            affected_accounts = set(line.account_id for line in voucher_lines)
            for account_id in affected_accounts:
                self._recalculate_account_balance(account_id, session)
            
            if should_close:
                session.commit()
            
            logger.info(f"Created {len(ledger_entries)} ledger entries for voucher {voucher_id}", self.logger_name)
            return ledger_entries
        finally:
            if should_close:
                session.close()
    
    @ExceptionMiddleware.handle_exceptions("LedgerService")
    def get_ledger_entries(self, filters: dict, pagination: dict):
        """Get ledger entries with filters and pagination"""
        from sqlalchemy.orm import joinedload
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(Ledger).options(
                joinedload(Ledger.account),
                joinedload(Ledger.voucher).joinedload(Voucher.voucher_type)
            ).filter(
                Ledger.tenant_id == tenant_id,
                Ledger.is_deleted == False
            )
            
            if filters.get('account_id'):
                query = query.filter(Ledger.account_id == filters['account_id'])
            
            if filters.get('from_date'):
                query = query.filter(Ledger.transaction_date >= filters['from_date'])
            
            if filters.get('to_date'):
                query = query.filter(Ledger.transaction_date <= filters['to_date'])
            
            if filters.get('is_reconciled') is not None:
                query = query.filter(Ledger.is_reconciled == filters['is_reconciled'])
            
            if filters.get('reference_type'):
                query = query.filter(Ledger.reference_type == filters['reference_type'])
            
            query = query.order_by(Ledger.transaction_date.desc(), Ledger.id.desc())
            
            total = query.count()
            entries = query.offset(pagination['offset']).limit(pagination['per_page']).all()
            
            # Convert to dicts within session
            result = []
            for entry in entries:
                result.append({
                    'id': entry.id,
                    'account_id': entry.account_id,
                    'account_name': entry.account.name if entry.account else '',
                    'voucher_id': entry.voucher_id,
                    'voucher_number': entry.voucher.voucher_number if entry.voucher else '',
                    'voucher_type': entry.voucher.voucher_type.name if entry.voucher and entry.voucher.voucher_type else '',
                    'transaction_date': entry.transaction_date,
                    'debit_amount': entry.debit_amount or 0,
                    'credit_amount': entry.credit_amount or 0,
                    'balance': entry.balance or 0,
                    'narration': entry.narration or '',
                    'reference_type': entry.reference_type,
                    'reference_number': entry.reference_number,
                    'is_reconciled': entry.is_reconciled,
                    'currency_id': entry.currency_id,
                    'debit_foreign': entry.debit_foreign,
                    'credit_foreign': entry.credit_foreign
                })
            
            return result, total
    
    @ExceptionMiddleware.handle_exceptions("LedgerService")
    def get_ledger_summary(self, filters: dict):
        """Get ledger summary with totals"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(
                func.sum(Ledger.debit_amount).label('total_debit'),
                func.sum(Ledger.credit_amount).label('total_credit')
            ).filter(
                Ledger.tenant_id == tenant_id,
                Ledger.is_deleted == False
            )
            
            if filters.get('account_id'):
                query = query.filter(Ledger.account_id == filters['account_id'])
            
            if filters.get('from_date'):
                query = query.filter(Ledger.transaction_date >= filters['from_date'])
            
            if filters.get('to_date'):
                query = query.filter(Ledger.transaction_date <= filters['to_date'])
            
            result = query.first()
            
            total_debit = float(result.total_debit or 0)
            total_credit = float(result.total_credit or 0)
            
            # Get opening balance if account_id and from_date provided
            opening_balance = 0
            if filters.get('account_id') and filters.get('from_date'):
                opening = session.query(
                    func.sum(Ledger.debit_amount - Ledger.credit_amount)
                ).filter(
                    Ledger.account_id == filters['account_id'],
                    Ledger.tenant_id == tenant_id,
                    Ledger.transaction_date < filters['from_date'],
                    Ledger.is_deleted == False
                ).scalar()
                opening_balance = float(opening or 0)
            
            return {
                'total_debit': total_debit,
                'total_credit': total_credit,
                'opening_balance': opening_balance,
                'closing_balance': opening_balance + total_debit - total_credit
            }
    
    @ExceptionMiddleware.handle_exceptions("LedgerService")
    def _recalculate_account_balance(self, account_id: int, session):
        """Recalculate running balance for an account"""
        tenant_id = session_manager.get_current_tenant_id()
        
        ledger_entries = session.query(Ledger).filter(
            Ledger.account_id == account_id,
            Ledger.tenant_id == tenant_id,
            Ledger.is_deleted == False
        ).order_by(Ledger.transaction_date.asc(), Ledger.id.asc()).all()
        
        running_balance = Decimal('0')
        for entry in ledger_entries:
            running_balance += (entry.debit_amount or 0) - (entry.credit_amount or 0)
            entry.balance = running_balance
        
        # Update account master balance
        account = session.query(AccountMaster).filter(
            AccountMaster.id == account_id,
            AccountMaster.tenant_id == tenant_id
        ).first()
        
        if account:
            account.current_balance = running_balance
            account.updated_at = datetime.utcnow()
            account.updated_by = session_manager.get_current_username()
    
    @ExceptionMiddleware.handle_exceptions("LedgerService")
    def recalculate_all_balances(self):
        """Recalculate balances for all accounts"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            accounts = session.query(AccountMaster).filter(
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.is_deleted == False
            ).all()
            
            updated_accounts = 0
            updated_entries = 0
            
            for account in accounts:
                ledger_entries = session.query(Ledger).filter(
                    Ledger.account_id == account.id,
                    Ledger.tenant_id == tenant_id,
                    Ledger.is_deleted == False
                ).order_by(Ledger.transaction_date.asc(), Ledger.id.asc()).all()
                
                running_balance = Decimal('0')
                for entry in ledger_entries:
                    running_balance += (entry.debit_amount or 0) - (entry.credit_amount or 0)
                    if entry.balance != running_balance:
                        entry.balance = running_balance
                        updated_entries += 1
                
                if account.current_balance != running_balance:
                    account.current_balance = running_balance
                    account.updated_at = datetime.utcnow()
                    account.updated_by = session_manager.get_current_username()
                    updated_accounts += 1
            
            session.commit()
            logger.info(f"Recalculated {updated_accounts} accounts, {updated_entries} entries", self.logger_name)
            
            return {
                'updated_accounts': updated_accounts,
                'updated_entries': updated_entries
            }
    
    @ExceptionMiddleware.handle_exceptions("LedgerService")
    def mark_reconciled(self, ledger_ids: list, reconciliation_ref: str = None):
        """Mark ledger entries as reconciled"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            entries = session.query(Ledger).filter(
                Ledger.id.in_(ledger_ids),
                Ledger.tenant_id == tenant_id
            ).all()
            
            for entry in entries:
                entry.is_reconciled = True
                entry.reconciliation_date = datetime.utcnow()
                entry.reconciliation_ref = reconciliation_ref
                entry.updated_by = session_manager.get_current_username()
            
            session.commit()
            logger.info(f"Marked {len(entries)} entries as reconciled", self.logger_name)
            
            return len(entries)
    
    @ExceptionMiddleware.handle_exceptions("LedgerService")
    def get_book_entries(self, book_type: str, filters: dict, pagination: dict):
        """Get book entries (Daily Book, Cash Book, Petty Cash Book) with filters and pagination"""
        from sqlalchemy.orm import joinedload
        from modules.account_module.models.entities import VoucherType
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(Ledger).options(
                joinedload(Ledger.account),
                joinedload(Ledger.voucher).joinedload(Voucher.voucher_type)
            ).filter(
                Ledger.tenant_id == tenant_id,
                Ledger.is_deleted == False,
                Ledger.is_posted == True
            )
            
            # Apply book type filter
            if book_type == 'CASH_BOOK':
                # Get cash accounts
                cash_accounts = session.query(AccountMaster.id).filter(
                    AccountMaster.tenant_id == tenant_id,
                    AccountMaster.is_deleted == False,
                    and_(
                        or_(
                            AccountMaster.code.ilike('%CASH%'),
                            AccountMaster.name.ilike('%CASH%'),
                            AccountMaster.system_code.ilike('%CASH%')
                        ),
                        AccountMaster.account_type == 'ASSET'
                    )
                ).all()
                account_ids = [acc.id for acc in cash_accounts]
                if account_ids:
                    query = query.filter(Ledger.account_id.in_(account_ids))
                else:
                    return [], 0
                    
            elif book_type == 'PETTY_CASH_BOOK':
                # Get petty cash accounts
                petty_cash_accounts = session.query(AccountMaster.id).filter(
                    AccountMaster.tenant_id == tenant_id,
                    AccountMaster.is_deleted == False,
                    and_(
                        or_(
                            AccountMaster.code.ilike('%PETTY%'),
                            AccountMaster.name.ilike('%PETTY%'),
                            AccountMaster.system_code.ilike('%PETTY%')
                        ),
                        AccountMaster.account_type == 'ASSET'
                    )
                ).all()
                account_ids = [acc.id for acc in petty_cash_accounts]
                if account_ids:
                    query = query.filter(Ledger.account_id.in_(account_ids))
                else:
                    return [], 0
            
            # DAILY_BOOK shows all transactions (no additional filter)
            
            # Apply additional filters
            if filters.get('account_id'):
                query = query.filter(Ledger.account_id == filters['account_id'])
            
            if filters.get('from_date'):
                query = query.filter(Ledger.transaction_date >= filters['from_date'])
            
            if filters.get('to_date'):
                query = query.filter(Ledger.transaction_date <= filters['to_date'])
            
            if filters.get('reference_type'):
                query = query.filter(Ledger.reference_type == filters['reference_type'])
            
            if filters.get('voucher_type'):
                voucher_ids = session.query(Voucher.id).join(VoucherType).filter(
                    VoucherType.code == filters['voucher_type'],
                    Voucher.tenant_id == tenant_id
                ).all()
                if voucher_ids:
                    query = query.filter(Ledger.voucher_id.in_([v.id for v in voucher_ids]))
            
            query = query.order_by(Ledger.transaction_date.desc(), Ledger.id.desc())
            
            total = query.count()
            entries = query.offset(pagination['offset']).limit(pagination['per_page']).all()
            
            # Convert to dicts
            result = []
            for entry in entries:
                result.append({
                    'id': entry.id,
                    'account_id': entry.account_id,
                    'account_name': entry.account.name if entry.account else '',
                    'account_code': entry.account.code if entry.account else '',
                    'voucher_id': entry.voucher_id,
                    'voucher_number': entry.voucher.voucher_number if entry.voucher else '',
                    'voucher_type': entry.voucher.voucher_type.name if entry.voucher and entry.voucher.voucher_type else '',
                    'voucher_type_code': entry.voucher.voucher_type.code if entry.voucher and entry.voucher.voucher_type else '',
                    'transaction_date': entry.transaction_date,
                    'posting_date': entry.posting_date,
                    'debit_amount': entry.debit_amount or 0,
                    'credit_amount': entry.credit_amount or 0,
                    'balance': entry.balance or 0,
                    'narration': entry.narration or '',
                    'reference_type': entry.reference_type,
                    'reference_number': entry.reference_number,
                    'currency_id': entry.currency_id,
                    'debit_foreign': entry.debit_foreign,
                    'credit_foreign': entry.credit_foreign
                })
            
            return result, total
