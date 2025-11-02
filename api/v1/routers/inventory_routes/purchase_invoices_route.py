from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text, or_
import math

router = APIRouter()



# Purchase Invoice
@router.get("/purchase-invoices", response_model=PaginatedResponse)
async def get_purchase_invoices(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = """
            SELECT pi.*, s.name as supplier_name 
            FROM purchase_invoices pi 
            JOIN suppliers s ON pi.supplier_id = s.id 
            WHERE pi.tenant_id = :tenant_id
        """
        params = {"tenant_id": current_user['tenant_id']}
        
        if pagination.search:
            query += " AND (pi.invoice_number ILIKE :search OR s.name ILIKE :search)"
            params["search"] = f"%{pagination.search}%"
        
        total = session.execute(text(query.replace("pi.*, s.name as supplier_name", "COUNT(*)")), params).scalar()
        query += f" ORDER BY pi.invoice_date DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": pagination.per_page, "offset": pagination.offset})
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
    
    return PaginatedResponse(success=True, message="Purchase invoices retrieved", data=data,
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/purchase-invoices", response_model=BaseResponse)
async def create_purchase_invoice(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        try:
            result = session.execute(text("""
                INSERT INTO purchase_invoices (invoice_number, invoice_date, supplier_id, 
                    subtotal, discount_amount, tax_amount, total_amount, balance_amount, 
                    status, notes, tenant_id, created_by)
                VALUES (:invoice_number, :invoice_date, :supplier_id, :subtotal, :discount_amount,
                    :tax_amount, :total_amount, :total_amount, :status, :notes, :tenant_id, :created_by)
                RETURNING id
            """), {**data, "tenant_id": current_user['tenant_id'], "created_by": current_user['username']})
            invoice_id = result.scalar()
            
            for item in data['items']:
                session.execute(text("""
                    INSERT INTO purchase_invoice_items (invoice_id, product_id, quantity, unit_price,
                        discount_amount, taxable_amount, cgst_amount, sgst_amount, igst_amount,
                        total_amount, tenant_id)
                    VALUES (:invoice_id, :product_id, :quantity, :unit_price, :discount_amount,
                        :taxable_amount, :cgst_amount, :sgst_amount, :igst_amount, :total_amount, :tenant_id)
                """), {**item, "invoice_id": invoice_id, "tenant_id": current_user['tenant_id']})
            
            session.commit()
            return BaseResponse(success=True, message="Purchase invoice created", data={"id": invoice_id})
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))
