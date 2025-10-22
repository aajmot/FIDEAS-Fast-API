from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
import io
import csv
import math

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.core.utils.pagination import PaginationParams, PaginatedResponse
from app.modules.inventory.services.product_service import ProductService
from app.db.models.inventory_models.product_model import Product

router = APIRouter()

@router.get("/products")
async def get_products(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    
    if pagination.search:
        search_term = f"%{pagination.search}%"
        query = query.filter(or_(
            Product.name.ilike(search_term),
            Product.code.ilike(search_term),
            Product.composition.ilike(search_term),
            Product.tags.ilike(search_term),
            Product.manufacturer.ilike(search_term),
            Product.hsn_code.ilike(search_term)
        ))
    
    total = query.count()
    products = query.offset(pagination.offset).limit(pagination.size).all()
    
    product_data = [{
        "id": product.id,
        "name": product.name,
        "code": product.code,
        "composition": product.composition,
        "price": float(product.price) if product.price else 0,
        "gst_percentage": float(product.gst_percentage) if product.gst_percentage else 0,
        "is_active": product.is_active
    } for product in products]
    
    return PaginatedResponse.create(
        items=product_data,
        total=total,
        page=pagination.page,
        size=pagination.size
    )

@router.post("/products")
async def create_product(
    product_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    product = product_service.create(product_data)
    return APIResponse.created({"id": product.id})

@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    product = product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return APIResponse.success({
        "id": product.id,
        "name": product.name,
        "code": product.code,
        "price": float(product.price) if product.price else 0,
        "is_active": product.is_active
    })

@router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    product_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    product = product_service.update(product_id, product_data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return APIResponse.success(message="Product updated successfully")

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    success = product_service.delete(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return APIResponse.success(message="Product deleted successfully")