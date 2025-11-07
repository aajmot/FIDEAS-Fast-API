from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text
import math

router = APIRouter()


@router.post("/credit-notes", response_model=BaseResponse)
async def create_credit_note(note_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Create credit note for sales returns with automatic accounting entries"""
    with db_manager.get_session() as session:
        try:
            # Insert credit note
            result = session.execute(text("""
                INSERT INTO credit_notes (note_number, note_date, customer_id, original_invoice_number, 
                    reason, subtotal, tax_amount, total_amount, tenant_id, created_by)
                VALUES (:note_number, :note_date, :customer_id, :original_invoice, :reason, 
                    :subtotal, :tax_amount, :total_amount, :tenant_id, :created_by)
                RETURNING id
            """), {
                "note_number": note_data['note_number'],
                "note_date": note_data['note_date'],
                "customer_id": note_data['customer_id'],
                "original_invoice": note_data.get('original_invoice_number'),
                "reason": note_data.get('reason', ''),
                "subtotal": note_data['subtotal'],
                "tax_amount": note_data['tax_amount'],
                "total_amount": note_data['total_amount'],
                "tenant_id": current_user['tenant_id'],
                "created_by": current_user['username']
            })

            note_id = result.fetchone()[0]

            # Insert items
            for item in note_data['items']:
                session.execute(text("""
                    INSERT INTO credit_note_items (credit_note_id, product_id, description, quantity, 
                        rate, tax_rate, tax_amount, amount, tenant_id)
                    VALUES (:note_id, :product_id, :description, :quantity, :rate, :tax_rate, :tax_amount, :amount, :tenant_id)
                """), {
                    "note_id": note_id,
                    "product_id": item.get('product_id'),
                    "description": item.get('description', ''),
                    "quantity": item['quantity'],
                    "rate": item['rate'],
                    "tax_rate": item.get('tax_rate', 0),
                    "tax_amount": item.get('tax_amount', 0),
                    "amount": item['amount'],
                    "tenant_id": current_user['tenant_id']
                })

            # Create accounting entries using transaction template
            template = session.execute(text("""
                SELECT id FROM transaction_templates 
                WHERE code = 'CREDIT_NOTE' AND tenant_id = :tenant_id
            """), {"tenant_id": current_user['tenant_id']}).fetchone()

            if template:
                # Get template rules
                rules = session.execute(text("""
                    SELECT account_type, account_id, entry_type, amount_source, narration
                    FROM transaction_template_rules
                    WHERE template_id = :template_id AND tenant_id = :tenant_id
                    ORDER BY line_number
                """), {"template_id": template[0], "tenant_id": current_user['tenant_id']}).fetchall()

                # Get voucher type
                voucher_type = session.execute(text("""
                    SELECT id FROM voucher_types WHERE code = 'CREDIT_NOTE' AND tenant_id = :tenant_id
                """), {"tenant_id": current_user['tenant_id']}).fetchone()

                if voucher_type:
                    # Create voucher
                    voucher_result = session.execute(text("""
                        INSERT INTO vouchers (voucher_number, voucher_type_id, voucher_date, 
                            reference_type, reference_id, reference_number, narration, total_amount, 
                            is_posted, tenant_id, created_by)
                        VALUES (:voucher_number, :voucher_type_id, :voucher_date, 'CREDIT_NOTE', :note_id, 
                            :note_number, :narration, :total_amount, TRUE, :tenant_id, :created_by)
                        RETURNING id
                    """), {
                        "voucher_number": f"V-{note_data['note_number']}",
                        "voucher_type_id": voucher_type[0],
                        "voucher_date": note_data['note_date'],
                        "note_id": note_id,
                        "note_number": note_data['note_number'],
                        "narration": note_data.get('reason', 'Credit note'),
                        "total_amount": note_data['total_amount'],
                        "tenant_id": current_user['tenant_id'],
                        "created_by": current_user['username']
                    })
                    voucher_id = voucher_result.fetchone()[0]

                    # Create ledger entries based on template rules
                    for rule in rules:
                        account_id = rule[1] if rule[1] else session.execute(text("""
                            SELECT account_id FROM account_configurations 
                            WHERE account_type = :account_type AND tenant_id = :tenant_id AND is_deleted = FALSE
                        """), {"account_type": rule[0], "tenant_id": current_user['tenant_id']}).scalar()

                        if account_id:
                            amount = note_data['total_amount'] if rule[3] == 'TOTAL_AMOUNT' else note_data['subtotal']
                            debit = amount if rule[2] == 'DEBIT' else 0
                            credit = amount if rule[2] == 'CREDIT' else 0

                            session.execute(text("""
                                INSERT INTO ledgers (account_id, voucher_id, transaction_date, 
                                    debit_amount, credit_amount, narration, tenant_id)
                                VALUES (:account_id, :voucher_id, :transaction_date, 
                                    :debit, :credit, :narration, :tenant_id)
                            """), {
                                "account_id": account_id,
                                "voucher_id": voucher_id,
                                "transaction_date": note_data['note_date'],
                                "debit": debit,
                                "credit": credit,
                                "narration": rule[4],
                                "tenant_id": current_user['tenant_id']
                            })

            session.commit()

            return BaseResponse(
                success=True,
                message="Credit note created successfully with accounting entries",
                data={"id": note_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/credit-notes", response_model=PaginatedResponse)
async def get_credit_notes(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    """Get all credit notes"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT cn.id, cn.note_number, cn.note_date, c.name as customer_name, cn.total_amount, cn.reason
            FROM credit_notes cn
            LEFT JOIN customers c ON cn.customer_id = c.id
            WHERE cn.tenant_id = :tenant_id AND cn.is_deleted = FALSE
            ORDER BY cn.note_date DESC
            LIMIT :limit OFFSET :offset
        """), {"tenant_id": current_user['tenant_id'], "limit": pagination.per_page, "offset": pagination.offset})

        notes = [{"id": r[0], "note_number": r[1], "date": r[2].isoformat(), "customer": r[3], "amount": float(r[4]), "reason": r[5]} for r in result]

        total = session.execute(text("SELECT COUNT(*) FROM credit_notes WHERE tenant_id = :tenant_id AND is_deleted = FALSE"), 
                               {"tenant_id": current_user['tenant_id']}).scalar()

        return PaginatedResponse(
            success=True,
            message="Credit notes retrieved successfully",
            data=notes,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(total / pagination.per_page)
        )
