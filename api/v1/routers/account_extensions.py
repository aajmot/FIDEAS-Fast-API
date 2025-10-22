"""
Additional endpoints for Critical Gap Features
Add these to account.py router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from datetime import datetime
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text, func
import math

router = APIRouter()

# Contra Voucher Endpoints
@router.post("/contra", response_model=BaseResponse)
async def create_contra(contra_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Create contra voucher for cash/bank transfers"""
    from modules.account_module.models.entities import Voucher, VoucherType, Ledger, AccountMaster
    
    with db_manager.get_session() as session:
        try:
            # Validate accounts are cash/bank type
            from_account = session.query(AccountMaster).filter(AccountMaster.id == contra_data['from_account_id']).first()
            to_account = session.query(AccountMaster).filter(AccountMaster.id == contra_data['to_account_id']).first()
            
            if not from_account or not to_account:
                raise HTTPException(status_code=400, detail="Invalid accounts")
            
            # Get Contra voucher type
            voucher_type = session.query(VoucherType).filter(
                VoucherType.code == 'CONTRA',
                VoucherType.tenant_id == current_user['tenant_id']
            ).first()
            
            # Create voucher
            voucher = Voucher(
                voucher_number=contra_data['voucher_number'],
                voucher_type_id=voucher_type.id,
                voucher_date=datetime.fromisoformat(contra_data['date']),
                narration=contra_data.get('narration', ''),
                total_amount=contra_data['amount'],
                is_posted=True,
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(voucher)
            session.flush()
            
            # Create ledger entries (debit to_account, credit from_account)
            ledger_to = Ledger(
                account_id=contra_data['to_account_id'],
                voucher_id=voucher.id,
                transaction_date=datetime.fromisoformat(contra_data['date']),
                debit_amount=contra_data['amount'],
                credit_amount=0,
                narration=contra_data.get('narration', ''),
                tenant_id=current_user['tenant_id']
            )
            session.add(ledger_to)
            
            ledger_from = Ledger(
                account_id=contra_data['from_account_id'],
                voucher_id=voucher.id,
                transaction_date=datetime.fromisoformat(contra_data['date']),
                debit_amount=0,
                credit_amount=contra_data['amount'],
                narration=contra_data.get('narration', ''),
                tenant_id=current_user['tenant_id']
            )
            session.add(ledger_from)
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Contra voucher created successfully",
                data={"id": voucher.id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.get("/contra", response_model=PaginatedResponse)
async def get_contra_vouchers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    """Get all contra vouchers"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT v.id, v.voucher_number, v.voucher_date, v.total_amount, v.narration
            FROM vouchers v
            JOIN voucher_types vt ON v.voucher_type_id = vt.id
            WHERE vt.code = 'CONTRA' AND v.tenant_id = :tenant_id AND v.is_deleted = FALSE
            ORDER BY v.voucher_date DESC
            LIMIT :limit OFFSET :offset
        """), {"tenant_id": current_user['tenant_id'], "limit": pagination.per_page, "offset": pagination.offset})
        
        vouchers = [{"id": r[0], "voucher_number": r[1], "date": r[2].isoformat(), "amount": float(r[3]), "narration": r[4]} for r in result]
        
        total = session.execute(text("""
            SELECT COUNT(*) FROM vouchers v
            JOIN voucher_types vt ON v.voucher_type_id = vt.id
            WHERE vt.code = 'CONTRA' AND v.tenant_id = :tenant_id AND v.is_deleted = FALSE
        """), {"tenant_id": current_user['tenant_id']}).scalar()
        
        return PaginatedResponse(
            success=True,
            message="Contra vouchers retrieved successfully",
            data=vouchers,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(total / pagination.per_page)
        )

# Credit Note Endpoints
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
                            SELECT account_id FROM account_type_mappings 
                            WHERE account_type = :account_type AND tenant_id = :tenant_id
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

# Debit Note Endpoints
@router.post("/debit-notes", response_model=BaseResponse)
async def create_debit_note(note_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Create debit note for purchase returns with automatic accounting entries"""
    with db_manager.get_session() as session:
        try:
            result = session.execute(text("""
                INSERT INTO debit_notes (note_number, note_date, supplier_id, original_invoice_number, 
                    reason, subtotal, tax_amount, total_amount, tenant_id, created_by)
                VALUES (:note_number, :note_date, :supplier_id, :original_invoice, :reason, 
                    :subtotal, :tax_amount, :total_amount, :tenant_id, :created_by)
                RETURNING id
            """), {
                "note_number": note_data['note_number'],
                "note_date": note_data['note_date'],
                "supplier_id": note_data['supplier_id'],
                "original_invoice": note_data.get('original_invoice_number'),
                "reason": note_data.get('reason', ''),
                "subtotal": note_data['subtotal'],
                "tax_amount": note_data['tax_amount'],
                "total_amount": note_data['total_amount'],
                "tenant_id": current_user['tenant_id'],
                "created_by": current_user['username']
            })
            
            note_id = result.fetchone()[0]
            
            for item in note_data['items']:
                session.execute(text("""
                    INSERT INTO debit_note_items (debit_note_id, product_id, description, quantity, 
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
                WHERE code = 'DEBIT_NOTE' AND tenant_id = :tenant_id
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
                    SELECT id FROM voucher_types WHERE code = 'DEBIT_NOTE' AND tenant_id = :tenant_id
                """), {"tenant_id": current_user['tenant_id']}).fetchone()
                
                if voucher_type:
                    # Create voucher
                    voucher_result = session.execute(text("""
                        INSERT INTO vouchers (voucher_number, voucher_type_id, voucher_date, 
                            reference_type, reference_id, reference_number, narration, total_amount, 
                            is_posted, tenant_id, created_by)
                        VALUES (:voucher_number, :voucher_type_id, :voucher_date, 'DEBIT_NOTE', :note_id, 
                            :note_number, :narration, :total_amount, TRUE, :tenant_id, :created_by)
                        RETURNING id
                    """), {
                        "voucher_number": f"V-{note_data['note_number']}",
                        "voucher_type_id": voucher_type[0],
                        "voucher_date": note_data['note_date'],
                        "note_id": note_id,
                        "note_number": note_data['note_number'],
                        "narration": note_data.get('reason', 'Debit note'),
                        "total_amount": note_data['total_amount'],
                        "tenant_id": current_user['tenant_id'],
                        "created_by": current_user['username']
                    })
                    voucher_id = voucher_result.fetchone()[0]
                    
                    # Create ledger entries based on template rules
                    for rule in rules:
                        account_id = rule[1] if rule[1] else session.execute(text("""
                            SELECT account_id FROM account_type_mappings 
                            WHERE account_type = :account_type AND tenant_id = :tenant_id
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
                message="Debit note created successfully with accounting entries",
                data={"id": note_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.get("/debit-notes", response_model=PaginatedResponse)
async def get_debit_notes(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    """Get all debit notes"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT dn.id, dn.note_number, dn.note_date, s.name as supplier_name, dn.total_amount, dn.reason
            FROM debit_notes dn
            LEFT JOIN suppliers s ON dn.supplier_id = s.id
            WHERE dn.tenant_id = :tenant_id AND dn.is_deleted = FALSE
            ORDER BY dn.note_date DESC
            LIMIT :limit OFFSET :offset
        """), {"tenant_id": current_user['tenant_id'], "limit": pagination.per_page, "offset": pagination.offset})
        
        notes = [{"id": r[0], "note_number": r[1], "date": r[2].isoformat(), "supplier": r[3], "amount": float(r[4]), "reason": r[5]} for r in result]
        
        total = session.execute(text("SELECT COUNT(*) FROM debit_notes WHERE tenant_id = :tenant_id AND is_deleted = FALSE"), 
                               {"tenant_id": current_user['tenant_id']}).scalar()
        
        return PaginatedResponse(
            success=True,
            message="Debit notes retrieved successfully",
            data=notes,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(total / pagination.per_page)
        )

# Aging Analysis Endpoints
@router.get("/aging-analysis/receivables", response_model=BaseResponse)
async def get_receivables_aging(current_user: dict = Depends(get_current_user)):
    """Get receivables aging analysis"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT 
                c.name as customer_name,
                SUM(CASE WHEN CURRENT_DATE - so.order_date <= 30 THEN so.total_amount ELSE 0 END) as days_0_30,
                SUM(CASE WHEN CURRENT_DATE - so.order_date BETWEEN 31 AND 60 THEN so.total_amount ELSE 0 END) as days_31_60,
                SUM(CASE WHEN CURRENT_DATE - so.order_date BETWEEN 61 AND 90 THEN so.total_amount ELSE 0 END) as days_61_90,
                SUM(CASE WHEN CURRENT_DATE - so.order_date > 90 THEN so.total_amount ELSE 0 END) as days_90_plus,
                SUM(so.total_amount) as total
            FROM sales_orders so
            JOIN customers c ON so.customer_id = c.id
            WHERE so.tenant_id = :tenant_id AND so.is_deleted = FALSE
            GROUP BY c.name
            ORDER BY total DESC
        """), {"tenant_id": current_user['tenant_id']})
        
        aging_data = [{
            "customer": r[0],
            "0-30": float(r[1]),
            "31-60": float(r[2]),
            "61-90": float(r[3]),
            "90+": float(r[4]),
            "total": float(r[5])
        } for r in result]
        
        return BaseResponse(
            success=True,
            message="Receivables aging retrieved successfully",
            data=aging_data
        )

@router.get("/aging-analysis/payables", response_model=BaseResponse)
async def get_payables_aging(current_user: dict = Depends(get_current_user)):
    """Get payables aging analysis"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT 
                s.name as supplier_name,
                SUM(CASE WHEN CURRENT_DATE - po.order_date <= 30 THEN po.total_amount ELSE 0 END) as days_0_30,
                SUM(CASE WHEN CURRENT_DATE - po.order_date BETWEEN 31 AND 60 THEN po.total_amount ELSE 0 END) as days_31_60,
                SUM(CASE WHEN CURRENT_DATE - po.order_date BETWEEN 61 AND 90 THEN po.total_amount ELSE 0 END) as days_61_90,
                SUM(CASE WHEN CURRENT_DATE - po.order_date > 90 THEN po.total_amount ELSE 0 END) as days_90_plus,
                SUM(po.total_amount) as total
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.tenant_id = :tenant_id AND po.is_deleted = FALSE
            GROUP BY s.name
            ORDER BY total DESC
        """), {"tenant_id": current_user['tenant_id']})
        
        aging_data = [{
            "supplier": r[0],
            "0-30": float(r[1]),
            "31-60": float(r[2]),
            "61-90": float(r[3]),
            "90+": float(r[4]),
            "total": float(r[5])
        } for r in result]
        
        return BaseResponse(
            success=True,
            message="Payables aging retrieved successfully",
            data=aging_data
        )

# TDS Management Endpoints
@router.get("/tds-sections", response_model=PaginatedResponse)
async def get_tds_sections(current_user: dict = Depends(get_current_user)):
    """Get all TDS sections"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT id, section_code, description, rate, threshold_limit, is_active
            FROM tds_sections
            WHERE tenant_id = :tenant_id
            ORDER BY section_code
        """), {"tenant_id": current_user['tenant_id']})
        
        sections = [{
            "id": r[0],
            "section_code": r[1],
            "description": r[2],
            "rate": float(r[3]),
            "threshold_limit": float(r[4]),
            "is_active": r[5]
        } for r in result]
        
        return PaginatedResponse(
            success=True,
            message="TDS sections retrieved successfully",
            data=sections,
            total=len(sections),
            page=1,
            per_page=len(sections),
            total_pages=1
        )

@router.post("/tds-sections", response_model=BaseResponse)
async def create_tds_section(section_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Create TDS section"""
    with db_manager.get_session() as session:
        try:
            result = session.execute(text("""
                INSERT INTO tds_sections (section_code, description, rate, threshold_limit, tenant_id)
                VALUES (:code, :description, :rate, :threshold, :tenant_id)
                RETURNING id
            """), {
                "code": section_data['section_code'],
                "description": section_data['description'],
                "rate": section_data['rate'],
                "threshold": section_data.get('threshold_limit', 0),
                "tenant_id": current_user['tenant_id']
            })
            
            section_id = result.fetchone()[0]
            session.commit()
            
            return BaseResponse(
                success=True,
                message="TDS section created successfully",
                data={"id": section_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/tds-calculate", response_model=BaseResponse)
async def calculate_tds(calc_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Calculate TDS amount"""
    with db_manager.get_session() as session:
        section = session.execute(text("""
            SELECT rate, threshold_limit FROM tds_sections
            WHERE section_code = :code AND tenant_id = :tenant_id
        """), {"code": calc_data['section_code'], "tenant_id": current_user['tenant_id']}).fetchone()
        
        if not section:
            raise HTTPException(status_code=404, detail="TDS section not found")
        
        amount = calc_data['amount']
        rate = float(section[0])
        threshold = float(section[1])
        
        tds_amount = (amount * rate / 100) if amount >= threshold else 0
        
        return BaseResponse(
            success=True,
            message="TDS calculated successfully",
            data={
                "amount": amount,
                "rate": rate,
                "threshold": threshold,
                "tds_amount": tds_amount,
                "net_amount": amount - tds_amount
            }
        )
