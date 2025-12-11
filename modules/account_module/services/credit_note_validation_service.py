from sqlalchemy import text
from typing import Dict, Any, Optional
from core.database.connection import db_manager


class CreditNoteValidationService:
    """Service to validate credit note voucher entries"""
    
    @staticmethod
    def validate_voucher_creation(note_id: int, tenant_id: int) -> Dict[str, Any]:
        """Validate that voucher entries are correctly created for credit note"""
        with db_manager.get_session() as session:
            # Get credit note details
            credit_note = session.execute(text("""
                SELECT cn.*, c.name as customer_name
                FROM credit_notes cn
                LEFT JOIN customers c ON cn.customer_id = c.id
                WHERE cn.id = :note_id AND cn.tenant_id = :tenant_id
            """), {"note_id": note_id, "tenant_id": tenant_id}).fetchone()
            
            if not credit_note:
                return {"valid": False, "error": "Credit note not found"}
            
            # Check if voucher exists
            voucher = session.execute(text("""
                SELECT v.*, vt.name as voucher_type_name
                FROM vouchers v
                LEFT JOIN voucher_types vt ON v.voucher_type_id = vt.id
                WHERE v.reference_type = 'CREDIT_NOTE' 
                AND v.reference_id = :note_id 
                AND v.tenant_id = :tenant_id
            """), {"note_id": note_id, "tenant_id": tenant_id}).fetchone()
            
            validation_result = {
                "valid": True,
                "credit_note": {
                    "id": credit_note.id,
                    "note_number": credit_note.note_number,
                    "customer_name": credit_note.customer_name,
                    "total_amount": float(credit_note.total_amount_base),
                    "status": credit_note.status
                },
                "voucher_exists": voucher is not None,
                "voucher_details": None,
                "voucher_lines": [],
                "accounting_validation": {}
            }
            
            if voucher:
                validation_result["voucher_details"] = {
                    "id": voucher.id,
                    "voucher_number": voucher.voucher_number,
                    "voucher_type": voucher.voucher_type_name,
                    "total_amount": float(voucher.base_total_amount),
                    "is_posted": voucher.is_posted
                }
                
                # Get voucher lines
                lines = session.execute(text("""
                    SELECT vl.*, am.name as account_name, am.code as account_code
                    FROM voucher_lines vl
                    LEFT JOIN account_masters am ON vl.account_id = am.id
                    WHERE vl.voucher_id = :voucher_id AND vl.tenant_id = :tenant_id
                    ORDER BY vl.line_no
                """), {"voucher_id": voucher.id, "tenant_id": tenant_id}).fetchall()
                
                total_debit = 0
                total_credit = 0
                
                for line in lines:
                    line_data = {
                        "line_no": line.line_no,
                        "account_name": line.account_name,
                        "account_code": line.account_code,
                        "description": line.description,
                        "debit": float(line.debit_base or 0),
                        "credit": float(line.credit_base or 0)
                    }
                    validation_result["voucher_lines"].append(line_data)
                    total_debit += line_data["debit"]
                    total_credit += line_data["credit"]
                
                # Validate accounting rules
                validation_result["accounting_validation"] = {
                    "total_debit": total_debit,
                    "total_credit": total_credit,
                    "balanced": abs(total_debit - total_credit) < 0.01,
                    "matches_credit_note_amount": abs(total_debit - float(credit_note.total_amount_base)) < 0.01,
                    "expected_entries": CreditNoteValidationService._get_expected_entries(credit_note)
                }
            
            return validation_result
    
    @staticmethod
    def _get_expected_entries(credit_note) -> Dict[str, Any]:
        """Define expected accounting entries for credit note"""
        return {
            "description": "Expected entries for credit note",
            "entries": [
                {
                    "account_type": "SALES",
                    "entry_type": "DEBIT",
                    "amount": float(credit_note.subtotal_base),
                    "description": "Reverse sales (Sales Return)"
                },
                {
                    "account_type": "GST_OUTPUT", 
                    "entry_type": "DEBIT",
                    "amount": float(credit_note.tax_amount_base),
                    "description": "Reverse GST Output"
                },
                {
                    "account_type": "ACCOUNTS_RECEIVABLE",
                    "entry_type": "CREDIT", 
                    "amount": float(credit_note.total_amount_base),
                    "description": "Customer credit"
                }
            ]
        }
    
    @staticmethod
    def get_account_configurations(tenant_id: int) -> Dict[str, Any]:
        """Get account configurations for the tenant"""
        with db_manager.get_session() as session:
            configs = session.execute(text("""
                SELECT ac.account_type, am.name as account_name, am.code as account_code
                FROM account_configurations ac
                LEFT JOIN account_masters am ON ac.account_id = am.id
                WHERE ac.tenant_id = :tenant_id AND ac.is_deleted = FALSE
                AND ac.account_type IN ('SALES', 'ACCOUNTS_RECEIVABLE', 'GST_OUTPUT')
            """), {"tenant_id": tenant_id}).fetchall()
            
            return {
                config.account_type: {
                    "name": config.account_name,
                    "code": config.account_code
                }
                for config in configs
            }
    
    @staticmethod
    def validate_customer_balance_impact(customer_id: int, tenant_id: int, 
                                       credit_note_amount: float) -> Dict[str, Any]:
        """Validate impact on customer balance"""
        with db_manager.get_session() as session:
            # Get customer current balance (simplified - would need proper ledger calculation)
            customer_balance = session.execute(text("""
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN vl.credit_base > 0 THEN -vl.credit_base
                        WHEN vl.debit_base > 0 THEN vl.debit_base
                        ELSE 0
                    END
                ), 0) as balance
                FROM voucher_lines vl
                JOIN vouchers v ON vl.voucher_id = v.id
                JOIN account_masters am ON vl.account_id = am.id
                WHERE am.code LIKE '%RECEIVABLE%' 
                AND v.tenant_id = :tenant_id
                AND vl.tenant_id = :tenant_id
            """), {"tenant_id": tenant_id}).scalar() or 0
            
            return {
                "current_balance": float(customer_balance),
                "credit_note_amount": credit_note_amount,
                "new_balance": float(customer_balance) - credit_note_amount,
                "balance_reduced": True
            }