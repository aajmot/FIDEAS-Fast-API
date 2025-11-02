from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any, List
import csv
import io
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from modules.inventory_module.models.warehouse_entity import Warehouse, StockByLocation, StockTransfer, StockTransferItem
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

@router.get("/stock-transfers", response_model=PaginatedResponse)
async def get_stock_transfers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = session.query(StockTransfer).options(
            joinedload(StockTransfer.from_warehouse),
            joinedload(StockTransfer.to_warehouse)
        ).filter(StockTransfer.tenant_id == current_user['tenant_id'])
        
        total = query.count()
        transfers = query.order_by(StockTransfer.transfer_date.desc()).offset(pagination.offset).limit(pagination.per_page).all()
        
        data = [{
            "id": st.id,
            "transfer_number": st.transfer_number,
            "transfer_date": st.transfer_date,
            "from_warehouse_id": st.from_warehouse_id,
            "to_warehouse_id": st.to_warehouse_id,
            "status": st.status,
            "notes": st.notes,
            "created_at": st.created_at,
            "created_by": st.created_by,
            "from_warehouse": st.from_warehouse.name,
            "to_warehouse": st.to_warehouse.name
        } for st in transfers]
    
    return PaginatedResponse(success=True, message="Stock transfers retrieved", data=data,
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.get("/stock-transfers/{transfer_id}", response_model=BaseResponse)
async def get_stock_transfer(transfer_id: int, current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        transfer = session.query(StockTransfer).options(
            joinedload(StockTransfer.from_warehouse),
            joinedload(StockTransfer.to_warehouse),
            joinedload(StockTransfer.items).joinedload(StockTransferItem.product)
        ).filter(
            StockTransfer.id == transfer_id,
            StockTransfer.tenant_id == current_user['tenant_id']
        ).first()
        
        if not transfer:
            raise HTTPException(404, "Stock transfer not found")
        
        data = {
            "id": transfer.id,
            "transfer_number": transfer.transfer_number,
            "transfer_date": transfer.transfer_date,
            "from_warehouse_id": transfer.from_warehouse_id,
            "to_warehouse_id": transfer.to_warehouse_id,
            "status": transfer.status,
            "notes": transfer.notes,
            "created_at": transfer.created_at,
            "created_by": transfer.created_by,
            "from_warehouse": transfer.from_warehouse.name,
            "to_warehouse": transfer.to_warehouse.name,
            "items": [{
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "batch_number": item.batch_number,
                "quantity": float(item.quantity),
                "serial_numbers": item.serial_numbers
            } for item in transfer.items]
        }
        
        return BaseResponse(success=True, message="Stock transfer retrieved", data=data)

@router.post("/stock-transfers", response_model=BaseResponse)
async def create_stock_transfer(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        try:
            transfer = StockTransfer(
                transfer_number=data.get("transfer_number"),
                transfer_date=data.get("transfer_date"),
                from_warehouse_id=data.get("from_warehouse_id"),
                to_warehouse_id=data.get("to_warehouse_id"),
                status="Created",  # Default status
                notes=data.get("notes"),
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(transfer)
            session.flush()
            
            for item in data.get('items', []):
                transfer_item = StockTransferItem(
                    transfer_id=transfer.id,
                    product_id=item.get("product_id"),
                    batch_number=item.get("batch_number"),
                    quantity=item.get("quantity"),
                    serial_numbers=item.get("serial_numbers"),
                    tenant_id=current_user['tenant_id']
                )
                session.add(transfer_item)
            
            session.commit()
            return BaseResponse(success=True, message="Stock transfer created", data={"id": transfer.id})
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))

@router.put("/stock-transfers/{transfer_id}", response_model=BaseResponse)
async def update_stock_transfer(transfer_id: int, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        transfer = session.query(StockTransfer).filter(
            StockTransfer.id == transfer_id,
            StockTransfer.tenant_id == current_user['tenant_id']
        ).first()
        
        if not transfer:
            raise HTTPException(404, "Stock transfer not found")
        
        # Update basic fields
        for key, value in data.items():
            if hasattr(transfer, key) and key not in ['id', 'tenant_id', 'created_at', 'created_by', 'items']:
                setattr(transfer, key, value)
        transfer.updated_by = current_user['username']
        
        # Handle items separately if provided
        if 'items' in data:
            # Delete existing items
            session.query(StockTransferItem).filter(StockTransferItem.transfer_id == transfer_id).delete()
            
            # Add new items
            for item_data in data['items']:
                item = StockTransferItem(
                    transfer_id=transfer_id,
                    product_id=item_data.get('product_id'),
                    batch_number=item_data.get('batch_number'),
                    quantity=item_data.get('quantity'),
                    serial_numbers=item_data.get('serial_numbers'),
                    tenant_id=current_user['tenant_id']
                )
                session.add(item)
        
        session.commit()
        return BaseResponse(success=True, message="Stock transfer updated")

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
