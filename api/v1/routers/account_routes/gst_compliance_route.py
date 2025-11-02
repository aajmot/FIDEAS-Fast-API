from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from core.database.connection import db_manager
from sqlalchemy import text

router = APIRouter()

@router.post("/generate-einvoice", response_model=BaseResponse)
async def generate_einvoice(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Generate e-invoice IRN"""
    with db_manager.get_session() as session:
        try:
            invoice_id = data['invoice_id']
            
            # Get invoice details
            invoice = session.execute(text("""
                SELECT si.*, c.name as customer_name, c.tax_id as customer_gstin
                FROM sales_invoices si
                JOIN customers c ON si.customer_id = c.id
                WHERE si.id = :id AND si.tenant_id = :tenant_id
            """), {"id": invoice_id, "tenant_id": current_user['tenant_id']}).fetchone()
            
            if not invoice:
                raise HTTPException(404, "Invoice not found")
            
            # TODO: Integrate with GST e-invoice API
            # For now, generate dummy IRN
            irn = f"IRN{datetime.now().strftime('%Y%m%d%H%M%S')}{invoice_id}"
            ack_no = f"ACK{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Update invoice
            session.execute(text("""
                UPDATE sales_invoices 
                SET is_einvoice = TRUE, einvoice_irn = :irn, einvoice_ack_no = :ack_no,
                    einvoice_ack_date = NOW()
                WHERE id = :id
            """), {"irn": irn, "ack_no": ack_no, "id": invoice_id})
            
            session.commit()
            return BaseResponse(success=True, message="E-invoice generated", 
                              data={"irn": irn, "ack_no": ack_no})
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))

@router.post("/generate-eway-bill", response_model=BaseResponse)
async def generate_eway_bill(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Generate e-way bill"""
    with db_manager.get_session() as session:
        try:
            # TODO: Integrate with e-way bill API
            eway_bill_no = f"EWB{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            result = session.execute(text("""
                INSERT INTO eway_bills (eway_bill_no, invoice_id, invoice_type, generated_date,
                    valid_upto, vehicle_number, distance, tenant_id)
                VALUES (:eway_bill_no, :invoice_id, :invoice_type, NOW(), 
                    NOW() + INTERVAL '3 days', :vehicle_number, :distance, :tenant_id)
                RETURNING id
            """), {**data, "eway_bill_no": eway_bill_no, "tenant_id": current_user['tenant_id']})
            
            # Update invoice
            session.execute(text("""
                UPDATE sales_invoices SET eway_bill_no = :eway_bill_no, eway_bill_date = NOW()
                WHERE id = :invoice_id
            """), {"eway_bill_no": eway_bill_no, "invoice_id": data['invoice_id']})
            
            session.commit()
            return BaseResponse(success=True, message="E-way bill generated", 
                              data={"eway_bill_no": eway_bill_no, "id": result.scalar()})
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))

@router.get("/gstr1-data", response_model=BaseResponse)
async def get_gstr1_data(return_period: str, current_user: dict = Depends(get_current_user)):
    """Get GSTR-1 return data for a period"""
    with db_manager.get_session() as session:
        # Get all invoices for the period
        invoices = session.execute(text("""
            SELECT si.*, c.tax_id as customer_gstin,
                   SUM(sii.taxable_amount) as taxable_value,
                   SUM(sii.cgst_amount) as cgst_amount,
                   SUM(sii.sgst_amount) as sgst_amount,
                   SUM(sii.igst_amount) as igst_amount
            FROM sales_invoices si
            JOIN customers c ON si.customer_id = c.id
            JOIN sales_invoice_items sii ON si.id = sii.invoice_id
            WHERE si.tenant_id = :tenant_id 
            AND TO_CHAR(si.invoice_date, 'YYYY-MM') = :period
            GROUP BY si.id, c.tax_id
        """), {"tenant_id": current_user['tenant_id'], "period": return_period}).fetchall()
        
        data = [dict(row._mapping) for row in invoices]
        
        # Calculate totals
        totals = {
            "total_taxable": sum(inv['taxable_value'] or 0 for inv in data),
            "total_cgst": sum(inv['cgst_amount'] or 0 for inv in data),
            "total_sgst": sum(inv['sgst_amount'] or 0 for inv in data),
            "total_igst": sum(inv['igst_amount'] or 0 for inv in data)
        }
        
        return BaseResponse(success=True, message="GSTR-1 data retrieved", 
                          data={"invoices": data, "totals": totals})

@router.get("/tds-deductions", response_model=BaseResponse)
async def get_tds_deductions(from_date: str = None, to_date: str = None, current_user: dict = Depends(get_current_user)):
    """Get TDS deductions"""
    with db_manager.get_session() as session:
        query = "SELECT * FROM tds_deductions WHERE tenant_id = :tenant_id"
        params = {"tenant_id": current_user['tenant_id']}
        
        if from_date:
            query += " AND deduction_date >= :from_date"
            params["from_date"] = from_date
        
        if to_date:
            query += " AND deduction_date <= :to_date"
            params["to_date"] = to_date
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
        
        return BaseResponse(success=True, message="TDS deductions retrieved", data=data)
