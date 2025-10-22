from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text, or_
import math

router = APIRouter()

# Payment Terms
@router.get("/payment-terms", response_model=PaginatedResponse)
async def get_payment_terms(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = "SELECT * FROM payment_terms WHERE tenant_id = :tenant_id"
        params = {"tenant_id": current_user['tenant_id']}
        
        if pagination.search:
            query += " AND name ILIKE :search"
            params["search"] = f"%{pagination.search}%"
        
        total = session.execute(text(query.replace("*", "COUNT(*)")), params).scalar()
        query += f" ORDER BY name LIMIT :limit OFFSET :offset"
        params.update({"limit": pagination.per_page, "offset": pagination.offset})
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
    
    return PaginatedResponse(success=True, message="Payment terms retrieved", data=data, 
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/payment-terms", response_model=BaseResponse)
async def create_payment_term(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        result = session.execute(text("""
            INSERT INTO payment_terms (name, code, days, description, tenant_id, created_by)
            VALUES (:name, :code, :days, :description, :tenant_id, :created_by)
            RETURNING id
        """), {**data, "tenant_id": current_user['tenant_id'], "created_by": current_user['username']})
        session.commit()
        return BaseResponse(success=True, message="Payment term created", data={"id": result.scalar()})

# Sales Invoice
@router.get("/sales-invoices", response_model=PaginatedResponse)
async def get_sales_invoices(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = """
            SELECT si.*, c.name as customer_name 
            FROM sales_invoices si 
            JOIN customers c ON si.customer_id = c.id 
            WHERE si.tenant_id = :tenant_id
        """
        params = {"tenant_id": current_user['tenant_id']}
        
        if pagination.search:
            query += " AND (si.invoice_number ILIKE :search OR c.name ILIKE :search)"
            params["search"] = f"%{pagination.search}%"
        
        total = session.execute(text(query.replace("si.*, c.name as customer_name", "COUNT(*)")), params).scalar()
        query += f" ORDER BY si.invoice_date DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": pagination.per_page, "offset": pagination.offset})
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
    
    return PaginatedResponse(success=True, message="Sales invoices retrieved", data=data,
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/sales-invoices", response_model=BaseResponse)
async def create_sales_invoice(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        try:
            # Calculate due date
            due_date = None
            if data.get('payment_term_id'):
                pt = session.execute(text("SELECT days FROM payment_terms WHERE id = :id"), 
                                   {"id": data['payment_term_id']}).fetchone()
                if pt:
                    due_date = datetime.fromisoformat(data['invoice_date']) + timedelta(days=pt[0])
            
            # Check credit limit
            customer = session.execute(text("""
                SELECT credit_limit, outstanding_balance, credit_hold 
                FROM customers WHERE id = :id AND tenant_id = :tenant_id
            """), {"id": data['customer_id'], "tenant_id": current_user['tenant_id']}).fetchone()
            
            if customer and customer[2]:  # credit_hold
                raise HTTPException(400, "Customer is on credit hold")
            
            if customer and customer[0] > 0:  # has credit limit
                if (customer[1] or 0) + data['total_amount'] > customer[0]:
                    raise HTTPException(400, "Credit limit exceeded")
            
            # Create invoice
            result = session.execute(text("""
                INSERT INTO sales_invoices (invoice_number, invoice_date, customer_id, payment_term_id, 
                    due_date, subtotal, discount_amount, tax_amount, total_amount, balance_amount, 
                    status, invoice_type, notes, tenant_id, created_by)
                VALUES (:invoice_number, :invoice_date, :customer_id, :payment_term_id, :due_date,
                    :subtotal, :discount_amount, :tax_amount, :total_amount, :total_amount,
                    :status, :invoice_type, :notes, :tenant_id, :created_by)
                RETURNING id
            """), {
                "invoice_number": data['invoice_number'],
                "invoice_date": data['invoice_date'],
                "customer_id": data['customer_id'],
                "payment_term_id": data.get('payment_term_id'),
                "due_date": due_date,
                "subtotal": data['subtotal'],
                "discount_amount": data.get('discount_amount', 0),
                "tax_amount": data['tax_amount'],
                "total_amount": data['total_amount'],
                "status": data.get('status', 'DRAFT'),
                "invoice_type": data.get('invoice_type', 'TAX_INVOICE'),
                "notes": data.get('notes'),
                "tenant_id": current_user['tenant_id'],
                "created_by": current_user['username']
            })
            invoice_id = result.scalar()
            
            # Create invoice items
            for item in data['items']:
                session.execute(text("""
                    INSERT INTO sales_invoice_items (invoice_id, product_id, description, quantity, 
                        unit_price, discount_amount, taxable_amount, cgst_rate, cgst_amount, 
                        sgst_rate, sgst_amount, igst_rate, igst_amount, total_amount, hsn_code, 
                        batch_number, serial_numbers, tenant_id)
                    VALUES (:invoice_id, :product_id, :description, :quantity, :unit_price, 
                        :discount_amount, :taxable_amount, :cgst_rate, :cgst_amount, :sgst_rate, 
                        :sgst_amount, :igst_rate, :igst_amount, :total_amount, :hsn_code, 
                        :batch_number, :serial_numbers, :tenant_id)
                """), {**item, "invoice_id": invoice_id, "tenant_id": current_user['tenant_id']})
            
            # Update customer outstanding
            session.execute(text("""
                UPDATE customers SET outstanding_balance = outstanding_balance + :amount 
                WHERE id = :id
            """), {"amount": data['total_amount'], "id": data['customer_id']})
            
            session.commit()
            return BaseResponse(success=True, message="Sales invoice created", data={"id": invoice_id})
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))

@router.get("/sales-invoices/{invoice_id}", response_model=BaseResponse)
async def get_sales_invoice(invoice_id: int, current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        invoice = session.execute(text("""
            SELECT si.*, c.name as customer_name 
            FROM sales_invoices si 
            JOIN customers c ON si.customer_id = c.id 
            WHERE si.id = :id AND si.tenant_id = :tenant_id
        """), {"id": invoice_id, "tenant_id": current_user['tenant_id']}).fetchone()
        
        if not invoice:
            raise HTTPException(404, "Invoice not found")
        
        items = session.execute(text("""
            SELECT sii.*, p.name as product_name 
            FROM sales_invoice_items sii 
            JOIN products p ON sii.product_id = p.id 
            WHERE sii.invoice_id = :id
        """), {"id": invoice_id}).fetchall()
        
        data = dict(invoice._mapping)
        data['items'] = [dict(item._mapping) for item in items]
        
        return BaseResponse(success=True, message="Invoice retrieved", data=data)

@router.post("/sales-invoices/convert-from-order/{order_id}", response_model=BaseResponse)
async def convert_order_to_invoice(order_id: int, current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        order = session.execute(text("""
            SELECT * FROM sales_orders WHERE id = :id AND tenant_id = :tenant_id
        """), {"id": order_id, "tenant_id": current_user['tenant_id']}).fetchone()
        
        if not order:
            raise HTTPException(404, "Order not found")
        
        # Generate invoice number
        now = datetime.now()
        invoice_number = f"INV-{current_user['tenant_id']}{now.strftime('%d%m%Y%H%M%S%f')[:17]}"
        
        # Create invoice from order
        result = session.execute(text("""
            INSERT INTO sales_invoices (invoice_number, invoice_date, customer_id, sales_order_id,
                subtotal, discount_amount, tax_amount, total_amount, balance_amount, status, 
                invoice_type, tenant_id, created_by)
            SELECT :invoice_number, CURRENT_DATE, customer_id, :order_id, 
                total_amount, discount_amount, 0, total_amount, total_amount, 'DRAFT', 
                'TAX_INVOICE', tenant_id, :created_by
            FROM sales_orders WHERE id = :order_id
            RETURNING id
        """), {"invoice_number": invoice_number, "order_id": order_id, "created_by": current_user['username']})
        invoice_id = result.scalar()
        
        # Copy items
        session.execute(text("""
            INSERT INTO sales_invoice_items (invoice_id, product_id, quantity, unit_price, 
                total_amount, tenant_id)
            SELECT :invoice_id, product_id, quantity, unit_price, total_price, tenant_id
            FROM sales_order_items WHERE sales_order_id = :order_id
        """), {"invoice_id": invoice_id, "order_id": order_id})
        
        session.commit()
        return BaseResponse(success=True, message="Invoice created from order", data={"id": invoice_id})

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
