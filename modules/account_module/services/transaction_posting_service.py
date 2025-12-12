"""
Transaction Posting Service
Handles automatic accounting entries based on transaction templates
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List
from decimal import Decimal
from .voucher_number_service import VoucherNumberService

class TransactionPostingService:
    
    @staticmethod
    def post_transaction(session: Session, transaction_type: str, transaction_data: Dict[str, Any], tenant_id: int) -> int:
        """
        Create accounting entries based on transaction template
        Returns voucher_id
        """
        # Get template for transaction type
        template = session.execute(text("""
            SELECT id FROM transaction_templates
            WHERE transaction_type = :type AND tenant_id = :tenant_id AND is_active = true
            LIMIT 1
        """), {"type": transaction_type, "tenant_id": tenant_id}).fetchone()
        
        if not template:
            raise Exception(f"No active template found for {transaction_type}")
        
        # Get template rules
        rules = session.execute(text("""
            SELECT line_number, account_id, account_type, entry_type, amount_source, narration
            FROM transaction_template_rules
            WHERE template_id = :template_id AND tenant_id = :tenant_id
            ORDER BY line_number
        """), {"template_id": template[0], "tenant_id": tenant_id}).fetchall()
        
        if not rules:
            raise Exception(f"No rules found for template")
        
        # Create voucher
        voucher_type = TransactionPostingService._get_voucher_type(transaction_type)
        voucher_id = TransactionPostingService._create_voucher(
            session, voucher_type, transaction_data, tenant_id
        )
        
        # Create journal
        journal_id = TransactionPostingService._create_journal(
            session, voucher_id, transaction_data, tenant_id
        )
        
        # Create journal details based on rules
        for rule in rules:
            account_id = TransactionPostingService._resolve_account(
                session, rule[1], rule[2], tenant_id
            )
            amount = TransactionPostingService._resolve_amount(
                transaction_data, rule[4]
            )
            
            TransactionPostingService._create_journal_detail(
                session, journal_id, account_id, rule[3], amount, rule[5], tenant_id
            )
        
        # Create ledger entries
        TransactionPostingService._create_ledger_entries(
            session, voucher_id, journal_id, transaction_data, tenant_id
        )
        
        return voucher_id
    
    @staticmethod
    def _get_voucher_type(transaction_type: str) -> str:
        mapping = {
            'SALES_ORDER': 'SAL',
            'PURCHASE_ORDER': 'PUR',
            'PRESCRIPTION': 'SAL',
            'DIAGNOSTIC_SALES': 'DIAG',
            'CLINIC_BILL': 'CLINIC'
        }
        return mapping.get(transaction_type, 'JV')
    
    @staticmethod
    def _resolve_account(session: Session, account_id: int, account_type: str, tenant_id: int) -> int:
        """Resolve account: specific account_id > type mapping > default"""
        if account_id:
            return account_id
        
        # Try account configuration
        mapping = session.execute(text("""
            SELECT account_id FROM account_configurations
            WHERE account_type = :type AND tenant_id = :tenant_id
        """), {"type": account_type, "tenant_id": tenant_id}).fetchone()
        
        if mapping:
            return mapping[0]
        
        # Fallback to default account
        default_codes = {
            'ACCOUNTS_RECEIVABLE': 'AR001',
            'ACCOUNTS_PAYABLE': 'AP001',
            'SALES_REVENUE': 'SR001',
            'INVENTORY': 'INV001',
            'COGS': 'PE001',
            'TAX_PAYABLE': 'STP001',
            'PHARMACY_REVENUE': 'SR001',
            'DIAGNOSTIC_REVENUE': 'SR001',
            'CLINIC_REVENUE': 'SR001'
        }
        
        code = default_codes.get(account_type, 'SR001')
        account = session.execute(text("""
            SELECT id FROM account_masters
            WHERE code = :code AND tenant_id = :tenant_id
        """), {"code": code, "tenant_id": tenant_id}).fetchone()
        
        if not account:
            raise Exception(f"No account found for type {account_type}")
        
        return account[0]
    
    @staticmethod
    def _resolve_amount(transaction_data: Dict[str, Any], amount_source: str) -> Decimal:
        """Resolve amount based on source"""
        mapping = {
            'TOTAL_AMOUNT': 'total_amount',
            'SUBTOTAL': 'subtotal',
            'TAX_AMOUNT': 'tax_amount',
            'DISCOUNT_AMOUNT': 'discount_amount'
        }
        
        field = mapping.get(amount_source, 'total_amount')
        return Decimal(str(transaction_data.get(field, 0)))
    
    @staticmethod
    def _create_voucher(session: Session, voucher_type_code: str, data: Dict[str, Any], tenant_id: int) -> int:
        """Create voucher record"""
        # Get voucher type id and prefix
        vtype = session.execute(text("""
            SELECT id, prefix FROM voucher_types WHERE code = :code AND tenant_id = :tenant_id
        """), {"code": voucher_type_code, "tenant_id": tenant_id}).fetchone()
        
        if not vtype:
            raise Exception(f"Voucher type {voucher_type_code} not found")
        
        # Generate voucher number using centralized service
        voucher_number = VoucherNumberService.generate_voucher_number(vtype[1], tenant_id)
        
        # Create voucher
        result = session.execute(text("""
            INSERT INTO vouchers (
                voucher_number, voucher_type_id, voucher_date, reference_type,
                reference_id, reference_number, total_amount, tenant_id, created_by, is_posted
            ) VALUES (
                :number, :type_id, CURRENT_TIMESTAMP, :ref_type, :ref_id, :ref_number,
                :amount, :tenant_id, :created_by, true
            ) RETURNING id
        """), {
            "number": voucher_number,
            "type_id": vtype[0],
            "ref_type": data.get('reference_type'),
            "ref_id": data.get('reference_id'),
            "ref_number": data.get('reference_number'),
            "amount": data.get('total_amount', 0),
            "tenant_id": tenant_id,
            "created_by": data.get('created_by', 'system')
        })
        
        return result.fetchone()[0]
    
    @staticmethod
    def _create_journal(session: Session, voucher_id: int, data: Dict[str, Any], tenant_id: int) -> int:
        """Create journal record"""
        result = session.execute(text("""
            INSERT INTO journals (
                voucher_id, journal_date, total_debit, total_credit, tenant_id
            ) VALUES (
                :voucher_id, CURRENT_TIMESTAMP, :debit, :credit, :tenant_id
            ) RETURNING id
        """), {
            "voucher_id": voucher_id,
            "debit": data.get('total_amount', 0),
            "credit": data.get('total_amount', 0),
            "tenant_id": tenant_id
        })
        
        return result.fetchone()[0]
    
    @staticmethod
    def _create_journal_detail(session: Session, journal_id: int, account_id: int, 
                               entry_type: str, amount: Decimal, narration: str, tenant_id: int):
        """Create journal detail record"""
        debit = amount if entry_type == 'DEBIT' else 0
        credit = amount if entry_type == 'CREDIT' else 0
        
        session.execute(text("""
            INSERT INTO journal_details (
                journal_id, account_id, debit_amount, credit_amount, narration, tenant_id
            ) VALUES (
                :journal_id, :account_id, :debit, :credit, :narration, :tenant_id
            )
        """), {
            "journal_id": journal_id,
            "account_id": account_id,
            "debit": debit,
            "credit": credit,
            "narration": narration,
            "tenant_id": tenant_id
        })
    
    @staticmethod
    def _create_ledger_entries(session: Session, voucher_id: int, journal_id: int, 
                               data: Dict[str, Any], tenant_id: int):
        """Create ledger entries from voucher lines using LedgerService"""
        from modules.account_module.services.ledger_service import LedgerService
        ledger_service = LedgerService()
        ledger_service.create_from_voucher(voucher_id, session)
