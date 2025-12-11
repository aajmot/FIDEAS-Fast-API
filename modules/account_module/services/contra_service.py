from core.database.connection import db_manager
from modules.account_module.models.entities import Voucher, VoucherType, Ledger, AccountMaster
from core.shared.utils.logger import logger
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime
from sqlalchemy import text
from typing import Dict, Any, List
import math

class ContraService:
    def __init__(self):
        self.logger_name = "ContraService"
    
    @ExceptionMiddleware.handle_exceptions("ContraService")
    def get_vouchers_by_type(self, voucher_type: str = "Contra", page: int = 1, per_page: int = 10, tenant_id: int = None) -> Dict[str, Any]:
        """Fetch vouchers by voucher type with pagination"""
        with db_manager.get_session() as session:
            offset = (page - 1) * per_page
            
            # Get voucher type ID by name
            voucher_type_obj = session.query(VoucherType).filter(
                VoucherType.name == voucher_type,
                VoucherType.tenant_id == tenant_id,
                VoucherType.is_deleted == False
            ).first()
            
            if not voucher_type_obj:
                return {
                    "vouchers": [],
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 0
                }
            
            # Get vouchers filtered by voucher_type_id
            result = session.execute(text("""
                SELECT v.id, v.voucher_number, v.voucher_date, v.base_total_amount, v.narration
                FROM vouchers v
                WHERE v.voucher_type_id = :voucher_type_id AND v.tenant_id = :tenant_id AND v.is_deleted = FALSE
                ORDER BY v.voucher_date DESC
                LIMIT :limit OFFSET :offset
            """), {
                "voucher_type_id": voucher_type_obj.id, 
                "tenant_id": tenant_id, 
                "limit": per_page, 
                "offset": offset
            })

            vouchers = [{
                "id": r[0], 
                "voucher_number": r[1], 
                "date": r[2].isoformat(), 
                "amount": float(r[3]), 
                "narration": r[4]
            } for r in result]

            # Get total count
            total = session.execute(text("""
                SELECT COUNT(*) FROM vouchers v
                WHERE v.voucher_type_id = :voucher_type_id AND v.tenant_id = :tenant_id AND v.is_deleted = FALSE
            """), {"voucher_type_id": voucher_type_obj.id, "tenant_id": tenant_id}).scalar()

            return {
                "vouchers": vouchers,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": math.ceil(total / per_page)
            }
    
    @ExceptionMiddleware.handle_exceptions("ContraService")
    def validate_contra_accounts(self, from_account_id: int, to_account_id: int, tenant_id: int) -> bool:
        """Validate that both accounts are cash/bank type accounts"""
        with db_manager.get_session() as session:
            
            # Check if accounts are the same
            if from_account_id == to_account_id:
                raise ValueError("From and To accounts cannot be the same")
            
            from_account = session.query(AccountMaster).filter(
                AccountMaster.id == from_account_id,
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.is_deleted == False,
                AccountMaster.is_active == True
            ).first()
            
            to_account = session.query(AccountMaster).filter(
                AccountMaster.id == to_account_id,
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.is_deleted == False,
                AccountMaster.is_active == True
            ).first()
            
            if not from_account:
                raise ValueError(f"From account with ID {from_account_id} not found or inactive")
            
            if not to_account:
                raise ValueError(f"To account with ID {to_account_id} not found or inactive")
            
            # Check if accounts are cash/bank type (assuming they should be ASSET type)
            if from_account.account_type != 'ASSET' or to_account.account_type != 'ASSET':
                raise ValueError("Contra vouchers can only be created between cash/bank accounts (ASSET type)")
            
            return True
    
    @ExceptionMiddleware.handle_exceptions("ContraService")
    def create_contra_voucher(self, contra_data: Dict[str, Any], tenant_id: int, current_user: str) -> Dict[str, Any]:
        """Create contra voucher with proper validation and ledger entries"""
        with db_manager.get_session() as session:
            
            # Validate required fields
            required_fields = ['from_account_id', 'to_account_id', 'amount', 'date']
            for field in required_fields:
                if field not in contra_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate accounts
            self.validate_contra_accounts(contra_data['from_account_id'], contra_data['to_account_id'], tenant_id)
            
            # Get Contra voucher type
            voucher_type = session.query(VoucherType).filter(
                VoucherType.name == 'Contra',
                VoucherType.tenant_id == tenant_id,
                VoucherType.is_deleted == False
            ).first()
            
            if not voucher_type:
                raise ValueError("Contra voucher type not found")
            
            # Use provided voucher number or generate new one
            voucher_number = contra_data.get('voucher_number') or self._generate_voucher_number(session, tenant_id)
            
            # Create voucher
            voucher = Voucher(
                voucher_number=voucher_number,
                voucher_type_id=voucher_type.id,
                voucher_date=datetime.fromisoformat(contra_data['date']),
                narration=contra_data.get('narration', ''),
                base_total_amount=contra_data['amount'],
                base_total_debit=contra_data['amount'],
                base_total_credit=contra_data['amount'],
                base_currency_id=1,  # Assuming default currency ID is 1
                is_posted=True,
                tenant_id=tenant_id,
                created_by=current_user
            )
            session.add(voucher)
            session.flush()
            
            # Create ledger entries (debit to_account, credit from_account)
            ledger_entries = [
                Ledger(
                    account_id=contra_data['to_account_id'],
                    voucher_id=voucher.id,
                    transaction_date=datetime.fromisoformat(contra_data['date']),
                    debit_amount=contra_data['amount'],
                    credit_amount=0,
                    balance=contra_data['amount'],
                    narration=contra_data.get('narration', ''),
                    tenant_id=tenant_id
                ),
                Ledger(
                    account_id=contra_data['from_account_id'],
                    voucher_id=voucher.id,
                    transaction_date=datetime.fromisoformat(contra_data['date']),
                    debit_amount=0,
                    credit_amount=contra_data['amount'],
                    balance=-contra_data['amount'],
                    narration=contra_data.get('narration', ''),
                    tenant_id=tenant_id
                )
            ]
            
            for ledger_entry in ledger_entries:
                session.add(ledger_entry)
            
            session.commit()
            
            logger.info(f"Contra voucher created: {voucher_number}", self.logger_name)
            
            return {
                "id": voucher.id,
                "voucher_number": voucher_number,
                "message": "Contra voucher created successfully"
            }
    
    def _generate_voucher_number(self, session, tenant_id: int) -> str:
        """Generate unique voucher number in format CNTR-[tenantid]ddmmyyyyhhmmssfff"""
        now = datetime.now()
        base_format = f"CNTR-{tenant_id}{now.strftime('%d%m%Y%H%M%S')}"
        
        # Get microseconds as 3-digit suffix
        microseconds = f"{now.microsecond // 1000:03d}"
        
        return f"{base_format}{microseconds}"
    
    @ExceptionMiddleware.handle_exceptions("ContraService")
    def get_contra_voucher_by_id(self, voucher_id: int, tenant_id: int) -> Dict[str, Any]:
        """Get a specific contra voucher by ID with its ledger entries"""
        with db_manager.get_session() as session:
            
            # Get contra voucher type ID first
            voucher_type_obj = session.query(VoucherType).filter(
                VoucherType.name == 'Contra',
                VoucherType.tenant_id == tenant_id,
                VoucherType.is_deleted == False
            ).first()
            
            if not voucher_type_obj:
                raise ValueError("Contra voucher type not found")
            
            # Get voucher with contra type
            result = session.execute(text("""
                SELECT v.id, v.voucher_number, v.voucher_date, v.base_total_amount, v.narration,
                       vt.name as voucher_type_name
                FROM vouchers v
                JOIN voucher_types vt ON v.voucher_type_id = vt.id
                WHERE v.id = :voucher_id AND v.voucher_type_id = :voucher_type_id 
                      AND v.tenant_id = :tenant_id AND v.is_deleted = FALSE
            """), {"voucher_id": voucher_id, "voucher_type_id": voucher_type_obj.id, "tenant_id": tenant_id})
            
            voucher_row = result.fetchone()
            if not voucher_row:
                raise ValueError(f"Contra voucher with ID {voucher_id} not found")
            
            # Get ledger entries
            ledger_result = session.execute(text("""
                SELECT l.account_id, am.name as account_name, l.debit_amount, l.credit_amount, l.narration
                FROM ledgers l
                JOIN account_masters am ON l.account_id = am.id
                WHERE l.voucher_id = :voucher_id AND l.tenant_id = :tenant_id
                ORDER BY l.debit_amount DESC
            """), {"voucher_id": voucher_id, "tenant_id": tenant_id})
            
            ledger_entries = [{
                "account_id": r[0],
                "account_name": r[1],
                "debit_amount": float(r[2]),
                "credit_amount": float(r[3]),
                "narration": r[4]
            } for r in ledger_result]
            
            return {
                "id": voucher_row[0],
                "voucher_number": voucher_row[1],
                "date": voucher_row[2].isoformat(),
                "amount": float(voucher_row[3]),
                "narration": voucher_row[4],
                "voucher_type": voucher_row[5],
                "ledger_entries": ledger_entries
            }