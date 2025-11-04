from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any, List
import csv
import io
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from modules.inventory_module.models.warehouse_entity import Warehouse, StockByLocation
from modules.inventory_module.models.stock_transfer_entity import StockTransfer, StockTransferItem
from modules.inventory_module.models.entities import Product
import math

router = APIRouter()

@router.get("/warehouses", response_model=PaginatedResponse)
async def get_warehouses(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = session.query(Warehouse).filter(Warehouse.tenant_id == current_user['tenant_id'])
        
        if pagination.search:
            query = query.filter(Warehouse.name.ilike(f"%{pagination.search}%"))
        
        total = query.count()
        warehouses = query.order_by(Warehouse.name).offset(pagination.offset).limit(pagination.per_page).all()
        
        data = [{
            "id": w.id, "name": w.name, "code": w.code, "address": w.address,
            "contact_person": w.contact_person, "phone": w.phone, "email": w.email,
            "is_active": w.is_active, "created_at": w.created_at, "updated_at": w.updated_at,
            "created_by": w.created_by, "updated_by": w.updated_by
        } for w in warehouses]
    
    return PaginatedResponse(success=True, message="Warehouses retrieved", data=data,
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/warehouses", response_model=BaseResponse)
async def create_warehouse(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        warehouse = Warehouse(
            name=data.get("name"),
            code=data.get("code"),
            address=data.get("address"),
            contact_person=data.get("contact_person"),
            phone=data.get("phone"),
            email=data.get("email"),
            tenant_id=current_user['tenant_id'],
            created_by=current_user['username']
        )
        session.add(warehouse)
        session.commit()
        return BaseResponse(success=True, message="Warehouse created", data={"id": warehouse.id})

@router.put("/warehouses/{warehouse_id}", response_model=BaseResponse)
async def update_warehouse(warehouse_id: int, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        warehouse = session.query(Warehouse).filter(
            Warehouse.id == warehouse_id,
            Warehouse.tenant_id == current_user['tenant_id']
        ).first()
        
        if not warehouse:
            raise HTTPException(404, "Warehouse not found")
        
        for key, value in data.items():
            if hasattr(warehouse, key):
                setattr(warehouse, key, value)
        warehouse.updated_by = current_user['username']
        
        session.commit()
        return BaseResponse(success=True, message="Warehouse updated")

@router.delete("/warehouses/{warehouse_id}", response_model=BaseResponse)
async def delete_warehouse(warehouse_id: int, current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        deleted = session.query(Warehouse).filter(
            Warehouse.id == warehouse_id,
            Warehouse.tenant_id == current_user['tenant_id']
        ).delete()
        
        if not deleted:
            raise HTTPException(404, "Warehouse not found")
        
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
            warehouses = []
            
            for row in csv_data:
                warehouse = Warehouse(
                    name=row.get("name"),
                    code=row.get("code"),
                    address=row.get("address"),
                    contact_person=row.get("contact_person"),
                    phone=row.get("phone"),
                    email=row.get("email"),
                    tenant_id=current_user['tenant_id'],
                    created_by=current_user['username']
                )
                warehouses.append(warehouse)
            
            session.add_all(warehouses)
            session.commit()
            return BaseResponse(success=True, message=f"{len(warehouses)} warehouses imported successfully")
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))

@router.get("/stock-by-location", response_model=BaseResponse)
async def get_stock_by_location(product_id: int = None, warehouse_id: int = None, current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = session.query(StockByLocation).options(
            joinedload(StockByLocation.product),
            joinedload(StockByLocation.warehouse)
        ).filter(StockByLocation.tenant_id == current_user['tenant_id'])
        
        if product_id:
            query = query.filter(StockByLocation.product_id == product_id)
        
        if warehouse_id:
            query = query.filter(StockByLocation.warehouse_id == warehouse_id)
        
        stock_locations = query.all()
        
        data = [{
            "id": sbl.id,
            "product_id": sbl.product_id,
            "warehouse_id": sbl.warehouse_id,
            "quantity": float(sbl.quantity),
            "available_quantity": float(sbl.available_quantity),
            "reserved_quantity": float(sbl.reserved_quantity or 0),
            "updated_at": sbl.updated_at,
            "product_name": sbl.product.name,
            "warehouse_name": sbl.warehouse.name
        } for sbl in stock_locations]
        
        return BaseResponse(success=True, message="Stock by location retrieved", data=data)

# ====================================================================
# COMMENTED OUT: Stock transfer endpoints moved to stock_transfers_route.py
# Use /api/v1/inventory/stock-transfers endpoints from stock_transfers_route.py instead
# ====================================================================

@router.get("/batches/near-expiry", response_model=BaseResponse)
async def get_near_expiry_batches(days: int = 30, current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = text(f"""
            SELECT pb.*, p.name as product_name
            FROM product_batches pb
            JOIN products p ON pb.product_id = p.id
            WHERE pb.tenant_id = :tenant_id 
            AND pb.expiry_date <= CURRENT_DATE + INTERVAL '{days} days'
            AND pb.quantity > 0
            ORDER BY pb.expiry_date ASC
        """)
        
        result = session.execute(query, {"tenant_id": current_user['tenant_id']})
        data = [dict(row._mapping) for row in result]
        
        return BaseResponse(success=True, message="Near expiry batches retrieved", data=data)

# COMMENTED OUT: Approve endpoint moved to stock_transfers service layer
# @router.post("/stock-transfers/{transfer_id}/approve", response_model=BaseResponse)
# async def approve_stock_transfer(transfer_id: int, current_user: dict = Depends(get_current_user)):
