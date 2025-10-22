from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text
import math

router = APIRouter()

@router.get("/categories", response_model=PaginatedResponse)
async def get_asset_categories(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = "SELECT * FROM asset_categories WHERE tenant_id = :tenant_id"
        params = {"tenant_id": current_user['tenant_id']}
        
        total = session.execute(text(query.replace("*", "COUNT(*)")), params).scalar()
        query += f" ORDER BY name LIMIT :limit OFFSET :offset"
        params.update({"limit": pagination.per_page, "offset": pagination.offset})
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
    
    return PaginatedResponse(success=True, message="Asset categories retrieved", data=data,
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/categories", response_model=BaseResponse)
async def create_asset_category(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        result = session.execute(text("""
            INSERT INTO asset_categories (name, code, depreciation_method, depreciation_rate, 
                useful_life_years, account_id, tenant_id)
            VALUES (:name, :code, :depreciation_method, :depreciation_rate, :useful_life_years,
                :account_id, :tenant_id)
            RETURNING id
        """), {**data, "tenant_id": current_user['tenant_id']})
        session.commit()
        return BaseResponse(success=True, message="Asset category created", data={"id": result.scalar()})

@router.get("/fixed-assets", response_model=PaginatedResponse)
async def get_fixed_assets(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = """
            SELECT fa.*, ac.name as category_name
            FROM fixed_assets fa
            JOIN asset_categories ac ON fa.category_id = ac.id
            WHERE fa.tenant_id = :tenant_id
        """
        params = {"tenant_id": current_user['tenant_id']}
        
        if pagination.search:
            query += " AND (fa.asset_number ILIKE :search OR fa.name ILIKE :search)"
            params["search"] = f"%{pagination.search}%"
        
        total = session.execute(text(query.replace("fa.*, ac.name as category_name", "COUNT(*)")), params).scalar()
        query += f" ORDER BY fa.purchase_date DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": pagination.per_page, "offset": pagination.offset})
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
    
    return PaginatedResponse(success=True, message="Fixed assets retrieved", data=data,
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/fixed-assets", response_model=BaseResponse)
async def create_fixed_asset(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        result = session.execute(text("""
            INSERT INTO fixed_assets (asset_number, name, category_id, purchase_date, purchase_cost,
                salvage_value, useful_life_years, depreciation_method, depreciation_rate, 
                book_value, status, location, serial_number, notes, tenant_id, created_by)
            VALUES (:asset_number, :name, :category_id, :purchase_date, :purchase_cost, :salvage_value,
                :useful_life_years, :depreciation_method, :depreciation_rate, :purchase_cost, 
                'ACTIVE', :location, :serial_number, :notes, :tenant_id, :created_by)
            RETURNING id
        """), {**data, "tenant_id": current_user['tenant_id'], "created_by": current_user['username']})
        session.commit()
        return BaseResponse(success=True, message="Fixed asset created", data={"id": result.scalar()})

@router.post("/calculate-depreciation", response_model=BaseResponse)
async def calculate_depreciation(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Calculate depreciation for a period"""
    with db_manager.get_session() as session:
        try:
            period_date = datetime.fromisoformat(data['period_date'])
            
            # Get all active assets
            assets = session.execute(text("""
                SELECT * FROM fixed_assets 
                WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
            """), {"tenant_id": current_user['tenant_id']}).fetchall()
            
            for asset in assets:
                # Calculate depreciation based on method
                if asset.depreciation_method == 'SLM':
                    # Straight Line Method
                    annual_dep = (asset.purchase_cost - asset.salvage_value) / asset.useful_life_years
                    monthly_dep = annual_dep / 12
                else:  # WDV
                    # Written Down Value Method
                    monthly_dep = asset.book_value * (asset.depreciation_rate / 100) / 12
                
                new_book_value = asset.book_value - monthly_dep
                
                # Insert depreciation schedule
                session.execute(text("""
                    INSERT INTO depreciation_schedule (asset_id, period_date, opening_value, 
                        depreciation_amount, closing_value, tenant_id)
                    VALUES (:asset_id, :period_date, :opening_value, :depreciation_amount, 
                        :closing_value, :tenant_id)
                """), {
                    "asset_id": asset.id,
                    "period_date": period_date,
                    "opening_value": asset.book_value,
                    "depreciation_amount": monthly_dep,
                    "closing_value": new_book_value,
                    "tenant_id": current_user['tenant_id']
                })
                
                # Update asset
                session.execute(text("""
                    UPDATE fixed_assets 
                    SET accumulated_depreciation = accumulated_depreciation + :dep,
                        book_value = :book_value
                    WHERE id = :id
                """), {"dep": monthly_dep, "book_value": new_book_value, "id": asset.id})
            
            session.commit()
            return BaseResponse(success=True, message="Depreciation calculated")
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))

@router.post("/{asset_id}/dispose", response_model=BaseResponse)
async def dispose_asset(asset_id: int, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        session.execute(text("""
            UPDATE fixed_assets 
            SET status = 'DISPOSED', disposal_date = :disposal_date, 
                disposal_value = :disposal_value, disposal_notes = :disposal_notes
            WHERE id = :id AND tenant_id = :tenant_id
        """), {**data, "id": asset_id, "tenant_id": current_user['tenant_id']})
        session.commit()
        return BaseResponse(success=True, message="Asset disposed")
