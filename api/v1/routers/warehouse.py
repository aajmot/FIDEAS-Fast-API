from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any, List
import csv
import io
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text
import math

router = APIRouter()

@router.get("/warehouses", response_model=PaginatedResponse)
async def get_warehouses(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = "SELECT * FROM warehouses WHERE tenant_id = :tenant_id"
        params = {"tenant_id": current_user['tenant_id']}
        
        if pagination.search:
            query += " AND name ILIKE :search"
            params["search"] = f"%{pagination.search}%"
        
        total = session.execute(text(query.replace("*", "COUNT(*)")), params).scalar()
        query += f" ORDER BY name LIMIT :limit OFFSET :offset"
        params.update({"limit": pagination.per_page, "offset": pagination.offset})
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
    
    return PaginatedResponse(success=True, message="Warehouses retrieved", data=data,
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/warehouses", response_model=BaseResponse)
async def create_warehouse(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        params = {
            "name": data.get("name"),
            "code": data.get("code"),
            "address": data.get("address"),
            "contact_person": data.get("contact_person"),
            "phone": data.get("phone"),
            "email": data.get("email"),
            "tenant_id": current_user['tenant_id'],
            "created_by": current_user['username']
        }
        result = session.execute(text("""
            INSERT INTO warehouses (name, code, address, contact_person, phone, email, tenant_id, created_by)
            VALUES (:name, :code, :address, :contact_person, :phone, :email, :tenant_id, :created_by)
            RETURNING id
        """), params)
        session.commit()
        return BaseResponse(success=True, message="Warehouse created", data={"id": result.scalar()})

@router.put("/warehouses/{warehouse_id}", response_model=BaseResponse)
async def update_warehouse(warehouse_id: int, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        session.execute(text("""
            UPDATE warehouses SET name = :name, code = :code, address = :address, 
                   contact_person = :contact_person, phone = :phone, email = :email, updated_by = :updated_by
            WHERE id = :id AND tenant_id = :tenant_id
        """), {**data, "id": warehouse_id, "tenant_id": current_user['tenant_id'], "updated_by": current_user['username']})
        session.commit()
        return BaseResponse(success=True, message="Warehouse updated")

@router.delete("/warehouses/{warehouse_id}", response_model=BaseResponse)
async def delete_warehouse(warehouse_id: int, current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        session.execute(text("""
            DELETE FROM warehouses WHERE id = :id AND tenant_id = :tenant_id
        """), {"id": warehouse_id, "tenant_id": current_user['tenant_id']})
        session.commit()
        return BaseResponse(success=True, message="Warehouse deleted")

@router.get("/warehouses/template", response_model=BaseResponse)
async def get_warehouse_template():
    template = [
        {"code": "WH001", "name": "Main Warehouse", "contact_person": "John Doe", "phone": "1234567890", "email": "warehouse@company.com", "address": "123 Main St, City, State"},
        {"code": "WH002", "name": "Secondary Warehouse", "contact_person": "Jane Smith", "phone": "0987654321", "email": "warehouse2@company.com", "address": "456 Oak Ave, City, State"}
    ]
    return BaseResponse(success=True, message="Warehouse template retrieved", data=template)

@router.post("/warehouses/import", response_model=BaseResponse)
async def import_warehouses(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Only CSV files are allowed")
    
    with db_manager.get_session() as session:
        try:
            content = await file.read()
            csv_data = csv.DictReader(io.StringIO(content.decode('utf-8')))
            created_count = 0
            
            for row in csv_data:
                params = {
                    "name": row.get("name"),
                    "code": row.get("code"),
                    "address": row.get("address"),
                    "contact_person": row.get("contact_person"),
                    "phone": row.get("phone"),
                    "email": row.get("email"),
                    "tenant_id": current_user['tenant_id'],
                    "created_by": current_user['username']
                }
                session.execute(text("""
                    INSERT INTO warehouses (name, code, address, contact_person, phone, email, tenant_id, created_by)
                    VALUES (:name, :code, :address, :contact_person, :phone, :email, :tenant_id, :created_by)
                """), params)
                created_count += 1
            
            session.commit()
            return BaseResponse(success=True, message=f"{created_count} warehouses imported successfully")
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))

@router.get("/stock-by-location", response_model=BaseResponse)
async def get_stock_by_location(product_id: int = None, warehouse_id: int = None, current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = """
            SELECT sbl.*, p.name as product_name, w.name as warehouse_name
            FROM stock_by_location sbl
            JOIN products p ON sbl.product_id = p.id
            JOIN warehouses w ON sbl.warehouse_id = w.id
            WHERE sbl.tenant_id = :tenant_id
        """
        params = {"tenant_id": current_user['tenant_id']}
        
        if product_id:
            query += " AND sbl.product_id = :product_id"
            params["product_id"] = product_id
        
        if warehouse_id:
            query += " AND sbl.warehouse_id = :warehouse_id"
            params["warehouse_id"] = warehouse_id
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
        
        return BaseResponse(success=True, message="Stock by location retrieved", data=data)

@router.get("/stock-transfers", response_model=PaginatedResponse)
async def get_stock_transfers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = """
            SELECT st.*, wf.name as from_warehouse, wt.name as to_warehouse
            FROM stock_transfers st
            JOIN warehouses wf ON st.from_warehouse_id = wf.id
            JOIN warehouses wt ON st.to_warehouse_id = wt.id
            WHERE st.tenant_id = :tenant_id
        """
        params = {"tenant_id": current_user['tenant_id']}
        
        total = session.execute(text(query.replace("st.*, wf.name as from_warehouse, wt.name as to_warehouse", "COUNT(*)")), params).scalar()
        query += f" ORDER BY st.transfer_date DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": pagination.per_page, "offset": pagination.offset})
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
    
    return PaginatedResponse(success=True, message="Stock transfers retrieved", data=data,
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/stock-transfers", response_model=BaseResponse)
async def create_stock_transfer(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        try:
            result = session.execute(text("""
                INSERT INTO stock_transfers (transfer_number, transfer_date, from_warehouse_id, 
                    to_warehouse_id, status, notes, tenant_id, created_by)
                VALUES (:transfer_number, :transfer_date, :from_warehouse_id, :to_warehouse_id,
                    :status, :notes, :tenant_id, :created_by)
                RETURNING id
            """), {**data, "tenant_id": current_user['tenant_id'], "created_by": current_user['username']})
            transfer_id = result.scalar()
            
            for item in data['items']:
                session.execute(text("""
                    INSERT INTO stock_transfer_items (transfer_id, product_id, batch_number, 
                        quantity, serial_numbers, tenant_id)
                    VALUES (:transfer_id, :product_id, :batch_number, :quantity, :serial_numbers, :tenant_id)
                """), {**item, "transfer_id": transfer_id, "tenant_id": current_user['tenant_id']})
            
            session.commit()
            return BaseResponse(success=True, message="Stock transfer created", data={"id": transfer_id})
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))

@router.post("/stock-transfers/{transfer_id}/approve", response_model=BaseResponse)
async def approve_stock_transfer(transfer_id: int, current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        try:
            # Get transfer details
            transfer = session.execute(text("""
                SELECT * FROM stock_transfers WHERE id = :id AND tenant_id = :tenant_id
            """), {"id": transfer_id, "tenant_id": current_user['tenant_id']}).fetchone()
            
            if not transfer:
                raise HTTPException(404, "Transfer not found")
            
            # Get items
            items = session.execute(text("""
                SELECT * FROM stock_transfer_items WHERE transfer_id = :id
            """), {"id": transfer_id}).fetchall()
            
            # Update stock by location
            for item in items:
                # Reduce from source
                session.execute(text("""
                    UPDATE stock_by_location 
                    SET quantity = quantity - :qty, available_quantity = available_quantity - :qty
                    WHERE product_id = :product_id AND warehouse_id = :from_wh AND tenant_id = :tenant_id
                """), {"qty": item.quantity, "product_id": item.product_id, 
                      "from_wh": transfer.from_warehouse_id, "tenant_id": current_user['tenant_id']})
                
                # Add to destination
                session.execute(text("""
                    INSERT INTO stock_by_location (product_id, warehouse_id, quantity, available_quantity, tenant_id)
                    VALUES (:product_id, :to_wh, :qty, :qty, :tenant_id)
                    ON CONFLICT (product_id, warehouse_id, tenant_id) 
                    DO UPDATE SET quantity = stock_by_location.quantity + :qty,
                                  available_quantity = stock_by_location.available_quantity + :qty
                """), {"product_id": item.product_id, "to_wh": transfer.to_warehouse_id, 
                      "qty": item.quantity, "tenant_id": current_user['tenant_id']})
            
            # Update transfer status
            session.execute(text("""
                UPDATE stock_transfers SET status = 'APPROVED', approved_at = NOW(), approved_by = :user
                WHERE id = :id
            """), {"id": transfer_id, "user": current_user['username']})
            
            session.commit()
            return BaseResponse(success=True, message="Stock transfer approved")
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))
