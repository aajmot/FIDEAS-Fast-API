from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
import math
from api.middleware.auth_middleware import get_current_user
from modules.inventory_module.services.product_service import ProductService
from modules.inventory_module.services.category_service import CategoryService
from modules.inventory_module.services.customer_service import CustomerService
from modules.inventory_module.services.supplier_service import SupplierService
from modules.inventory_module.services.unit_service import UnitService


router = APIRouter()

# Unit endpoints
@router.get("/units", response_model=PaginatedResponse)
async def get_units(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Unit
    
    with db_manager.get_session() as session:
        query = session.query(Unit).filter(
            Unit.tenant_id == current_user['tenant_id']
        )
        
        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                Unit.name.ilike(search_term),
                Unit.symbol.ilike(search_term)
            ))
        
        total = query.count()
        units = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        unit_data = [{
            "id": unit.id,
            "name": unit.name,
            "symbol": unit.symbol,
            "parent_id": unit.parent_id,
            "conversion_factor": float(unit.conversion_factor) if unit.conversion_factor else 1.0,
            "is_active": unit.is_active
        } for unit in units]
    
    return PaginatedResponse(
        success=True,
        message="Units retrieved successfully",
        data=unit_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )

@router.post("/units", response_model=BaseResponse)
async def create_unit(unit_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    unit_service = UnitService()
    unit = unit_service.create(unit_data)
    unit_id = unit.id
    return BaseResponse(
        success=True,
        message="Unit created successfully",
        data={"id": unit_id}
    )

@router.put("/units/{unit_id}", response_model=BaseResponse)
async def update_unit(unit_id: int, unit_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    unit_service = UnitService()
    unit = unit_service.update(unit_id, unit_data)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    return BaseResponse(success=True, message="Unit updated successfully")

@router.delete("/units/{unit_id}", response_model=BaseResponse)
async def delete_unit(unit_id: int, current_user: dict = Depends(get_current_user)):
    unit_service = UnitService()
    success = unit_service.delete(unit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    return BaseResponse(success=True, message="Unit deleted successfully")

# Product endpoints
@router.get("/products", response_model=PaginatedResponse)
async def get_products(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Product
    from core.shared.utils.session_manager import session_manager
    
    with db_manager.get_session() as session:
        query = session.query(Product)
        
        # Apply tenant filter
        tenant_id = session_manager.get_current_tenant_id()
        if tenant_id:
            query = query.filter(Product.tenant_id == tenant_id)
        
        # Apply search filter
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
        products = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        product_data = [{
            "id": product.id,
            "name": product.name,
            "code": product.code,
            "composition": product.composition,
            "tags": product.tags,
            "hsn_code": product.hsn_code,
            "schedule": product.schedule,
            "manufacturer": product.manufacturer,
            "is_discontinued": product.is_discontinued,
            "category_id": product.category_id,
            "subcategory_id": product.subcategory_id,
            "unit_id": product.unit_id,
            "price": float(product.price) if product.price else 0,
            "gst_percentage": float(product.gst_percentage) if product.gst_percentage else 0,
            "commission_type": product.commission_type,
            "commission_value": float(product.commission_value) if product.commission_value else None,
            "description": product.description,
            "is_active": product.is_active
        } for product in products]
    
    return PaginatedResponse(
        success=True,
        message="Products retrieved successfully",
        data=product_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )

@router.post("/products", response_model=BaseResponse)
async def create_product(product_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    # Validate commission_type
    commission_type = product_data.get('commission_type')
    if commission_type and commission_type not in ['', 'Percentage', 'Fixed']:
        raise HTTPException(status_code=400, detail="commission_type must be null/empty, 'Percentage', or 'Fixed'")
    
    product_service = ProductService()
    product = product_service.create(product_data)
    product_id = product.id
    return BaseResponse(
        success=True,
        message="Product created successfully",
        data={"id": product_id}
    )

@router.get("/products/get/{product_id}", response_model=BaseResponse)
async def get_product(product_id: int, current_user: dict = Depends(get_current_user)):
    product_service = ProductService()
    product = product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return BaseResponse(
        success=True,
        message="Product retrieved successfully",
        data={
            "id": product.id,
            "name": product.name,
            "code": product.code,
            "composition": product.composition,
            "tags": product.tags,
            "hsn_code": product.hsn_code,
            "schedule": product.schedule,
            "manufacturer": product.manufacturer,
            "is_discontinued": product.is_discontinued,
            "category_id": product.category_id,
            "subcategory_id": product.subcategory_id,
            "unit_id": product.unit_id,
            "price": float(product.price) if product.price else 0,
            "gst_percentage": float(product.gst_percentage) if product.gst_percentage else 0,
            "commission_type": product.commission_type,
            "commission_value": float(product.commission_value) if product.commission_value else None,
            "description": product.description,
            "is_active": product.is_active
        }
    )

@router.put("/products/update/{product_id}", response_model=BaseResponse)
async def update_product(product_id: int, product_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    # Validate commission_type
    commission_type = product_data.get('commission_type')
    if commission_type and commission_type not in ['', 'Percentage', 'Fixed']:
        raise HTTPException(status_code=400, detail="commission_type must be null/empty, 'Percentage', or 'Fixed'")
    
    # Convert empty strings to None for numeric fields
    if 'commission_value' in product_data and product_data['commission_value'] == '':
        product_data['commission_value'] = None
    
    product_service = ProductService()
    product = product_service.update(product_id, product_data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return BaseResponse(success=True, message="Product updated successfully")

@router.delete("/products/delete/{product_id}", response_model=BaseResponse)
async def delete_product(product_id: int, current_user: dict = Depends(get_current_user)):
    product_service = ProductService()
    success = product_service.delete(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return BaseResponse(success=True, message="Product deleted successfully")

# Category endpoints
@router.get("/categories", response_model=PaginatedResponse)
async def get_categories(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Category
    from core.shared.utils.session_manager import session_manager
    
    with db_manager.get_session() as session:
        query = session.query(Category)
        
        # Apply tenant filter
        tenant_id = session_manager.get_current_tenant_id()
        if tenant_id:
            query = query.filter(Category.tenant_id == tenant_id)
        
        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                Category.name.ilike(search_term),
                Category.description.ilike(search_term)
            ))
        
        total = query.count()
        categories = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        category_data = []
        for category in categories:
            parent_name = None
            if category.parent_id:
                parent = session.query(Category).filter(Category.id == category.parent_id).first()
                if parent:
                    parent_name = parent.name
            
            category_data.append({
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "parent_id": category.parent_id,
                "parent_name": parent_name,
                "is_active": category.is_active
            })
    
    return PaginatedResponse(
        success=True,
        message="Categories retrieved successfully",
        data=category_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )

@router.post("/categories", response_model=BaseResponse)
async def create_category(category_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    category_service = CategoryService()
    category = category_service.create(category_data)
    category_id = category.id  # Access id while session is still active
    return BaseResponse(
        success=True,
        message="Category created successfully",
        data={"id": category_id}
    )

@router.put("/categories/{category_id}", response_model=BaseResponse)
async def update_category(category_id: int, category_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    category_service = CategoryService()
    category = category_service.update(category_id, category_data)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return BaseResponse(success=True, message="Category updated successfully")

@router.delete("/categories/{category_id}", response_model=BaseResponse)
async def delete_category(category_id: int, current_user: dict = Depends(get_current_user)):
    category_service = CategoryService()
    success = category_service.delete(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return BaseResponse(success=True, message="Category deleted successfully")

# Customer endpoints
@router.get("/customers", response_model=PaginatedResponse)
async def get_customers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Customer
    
    with db_manager.get_session() as session:
        query = session.query(Customer).filter(
            Customer.tenant_id == current_user['tenant_id']
        )
        
        if pagination.search:
            query = query.filter(or_(
                Customer.name.ilike(f"%{pagination.search}%"),
                Customer.email.ilike(f"%{pagination.search}%"),
                Customer.phone.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        customers = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        customer_data = [{
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "age": customer.age,
            "address": customer.address,
            "tax_id": customer.tax_id,
            "is_active": customer.is_active
        } for customer in customers]
    
    return PaginatedResponse(
        success=True,
        message="Customers retrieved successfully",
        data=customer_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/customers", response_model=BaseResponse)
async def create_customer(customer_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    customer_service = CustomerService()
    customer = customer_service.create(customer_data)
    return BaseResponse(
        success=True,
        message="Customer created successfully",
        data={"id": customer}
    )

@router.put("/customers/{customer_id}", response_model=BaseResponse)
async def update_customer(customer_id: int, customer_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    customer_service = CustomerService()
    customer = customer_service.update(customer_id, customer_data)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return BaseResponse(success=True, message="Customer updated successfully")

@router.delete("/customers/{customer_id}", response_model=BaseResponse)
async def delete_customer(customer_id: int, current_user: dict = Depends(get_current_user)):
    customer_service = CustomerService()
    success = customer_service.delete(customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return BaseResponse(success=True, message="Customer deleted successfully")

# Supplier endpoints
@router.get("/suppliers", response_model=PaginatedResponse)
async def get_suppliers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Supplier
    
    with db_manager.get_session() as session:
        query = session.query(Supplier).filter(
            Supplier.tenant_id == current_user['tenant_id']
        )
        
        if pagination.search:
            query = query.filter(or_(
                Supplier.name.ilike(f"%{pagination.search}%"),
                Supplier.email.ilike(f"%{pagination.search}%"),
                Supplier.phone.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        suppliers = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        supplier_data = [{
            "id": supplier.id,
            "name": supplier.name,
            "phone": supplier.phone,
            "email": supplier.email,
            "tax_id": supplier.tax_id,
            "contact_person": supplier.contact_person,
            "address": supplier.address,
            "is_active": supplier.is_active
        } for supplier in suppliers]
    
    return PaginatedResponse(
        success=True,
        message="Suppliers retrieved successfully",
        data=supplier_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/suppliers", response_model=BaseResponse)
async def create_supplier(supplier_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    supplier_service = SupplierService()
    supplier = supplier_service.create(supplier_data)
    return BaseResponse(
        success=True,
        message="Supplier created successfully",
        data={"id": supplier}
    )

@router.put("/suppliers/{supplier_id}", response_model=BaseResponse)
async def update_supplier(supplier_id: int, supplier_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    supplier_service = SupplierService()
    supplier = supplier_service.update(supplier_id, supplier_data)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return BaseResponse(success=True, message="Supplier updated successfully")

@router.delete("/suppliers/{supplier_id}", response_model=BaseResponse)
async def delete_supplier(supplier_id: int, current_user: dict = Depends(get_current_user)):
    supplier_service = SupplierService()
    success = supplier_service.delete(supplier_id)
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return BaseResponse(success=True, message="Supplier deleted successfully")

# Purchase Order endpoints
@router.get("/purchase-orders", response_model=PaginatedResponse)
async def get_purchase_orders(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.purchase_order_service import PurchaseOrderService
    
    purchase_order_service = PurchaseOrderService()
    orders = purchase_order_service.get_all(page=pagination.page, page_size=pagination.per_page)
    total = purchase_order_service.get_total_count()
    
    order_data = [{
        "id": order.id,
        "po_number": order.po_number,
        "supplier_name": order.supplier_name,
        "order_date": order.order_date.isoformat() if order.order_date else None,
        "total_amount": float(order.total_amount),
        "status": order.status
    } for order in orders]
    
    return PaginatedResponse(
        success=True,
        message="Purchase orders retrieved successfully",
        data=order_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/purchase-orders", response_model=BaseResponse)
async def create_purchase_order(order_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.purchase_order_service import PurchaseOrderService
    from modules.account_module.services.transaction_posting_service import TransactionPostingService
    from core.database.connection import db_manager
    
    with db_manager.get_session() as session:
        purchase_order_service = PurchaseOrderService()
        order_id = purchase_order_service.create_with_items(order_data['order'], order_data['items'])
        
        # Post to accounting
        try:
            posting_data = {
                'reference_type': 'PURCHASE_ORDER',
                'reference_id': order_id,
                'reference_number': order_data['order'].get('po_number'),
                'total_amount': order_data['order'].get('total_amount'),
                'transaction_date': order_data['order'].get('order_date'),
                'created_by': current_user['username']
            }
            voucher_id = TransactionPostingService.post_transaction(
                session, 'PURCHASE_ORDER', posting_data, current_user['tenant_id']
            )
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Accounting posting failed: {e}")
        
        return BaseResponse(
            success=True,
            message="Purchase order created successfully",
            data={"id": order_id}
        )

@router.get("/purchase-orders/{order_id}", response_model=BaseResponse)
async def get_purchase_order(order_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import PurchaseOrder, PurchaseOrderItem, Product, Supplier
    
    with db_manager.get_session() as session:
        order = session.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        items = session.query(PurchaseOrderItem, Product).join(Product).filter(
            PurchaseOrderItem.purchase_order_id == order_id
        ).all()
        
        supplier = session.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        
        order_data = {
            "id": order.id,
            "po_number": order.po_number,
            "supplier_id": order.supplier_id,
            "supplier_name": supplier.name if supplier else "",
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "total_amount": float(order.total_amount),
            "discount_percent": float(order.discount_percent),
            "discount_amount": float(order.discount_amount),
            "roundoff": float(order.roundoff),
            "status": order.status,
            "items": [{
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "mrp": float(item.mrp),
                "gst_rate": float(item.gst_rate),
                "discount_percent": float(item.discount_percent),
                "discount_amount": float(item.discount_amount),
                "total_amount": float(item.total_amount)
            } for item, product in items]
        }
    
    return BaseResponse(
        success=True,
        message="Purchase order retrieved successfully",
        data=order_data
    )

@router.post("/purchase-orders/{order_id}/reverse", response_model=BaseResponse)
async def reverse_purchase_order(order_id: int, reason_data: Dict[str, str], current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.purchase_order_service import PurchaseOrderService
    
    purchase_order_service = PurchaseOrderService()
    success = purchase_order_service.reverse_order(order_id, reason_data.get('reason', ''))
    if not success:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    return BaseResponse(success=True, message="Purchase order reversed successfully")

# Sales Order endpoints
@router.get("/sales-orders", response_model=PaginatedResponse)
async def get_sales_orders(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.sales_order_service import SalesOrderService
    
    sales_order_service = SalesOrderService()
    orders = sales_order_service.get_all(page=pagination.page, page_size=pagination.per_page)
    total = sales_order_service.get_total_count()
    
    order_data = [{
        "id": order.id,
        "so_number": order.order_number,
        "customer_name": order.customer_name,
        "agency_id": getattr(order, 'agency_id', None),
        "agency_name": getattr(order, 'agency_name', None),
        "order_date": order.order_date.isoformat() if order.order_date else None,
        "total_amount": float(order.total_amount),
        "status": order.status
    } for order in orders]
    
    return PaginatedResponse(
        success=True,
        message="Sales orders retrieved successfully",
        data=order_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/sales-orders", response_model=BaseResponse)
async def create_sales_order(order_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.sales_order_service import SalesOrderService
    from modules.account_module.services.transaction_posting_service import TransactionPostingService
    from core.database.connection import db_manager
    
    with db_manager.get_session() as session:
        sales_order_service = SalesOrderService()
        order_id = sales_order_service.create_with_items(order_data['order'], order_data['items'])
        
        # Post to accounting
        try:
            posting_data = {
                'reference_type': 'SALES_ORDER',
                'reference_id': order_id,
                'reference_number': order_data['order'].get('order_number'),
                'total_amount': order_data['order'].get('total_amount'),
                'transaction_date': order_data['order'].get('order_date'),
                'created_by': current_user['username']
            }
            voucher_id = TransactionPostingService.post_transaction(
                session, 'SALES_ORDER', posting_data, current_user['tenant_id']
            )
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Accounting posting failed: {e}")
        
        return BaseResponse(
            success=True,
            message="Sales order created successfully",
            data={"id": order_id}
        )

@router.get("/sales-orders/{order_id}", response_model=BaseResponse)
async def get_sales_order(order_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import SalesOrder, SalesOrderItem, Product, Customer
    from modules.admin_module.models.agency import Agency
    
    with db_manager.get_session() as session:
        order = session.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Sales order not found")
        
        items = session.query(SalesOrderItem, Product).join(Product).filter(
            SalesOrderItem.sales_order_id == order_id
        ).all()
        
        customer = session.query(Customer).filter(Customer.id == order.customer_id).first()
        
        agency_name = None
        if order.agency_id:
            agency = session.query(Agency).filter(Agency.id == order.agency_id).first()
            if agency:
                agency_name = f"{agency.name} | {agency.phone}"
        
        order_data = {
            "id": order.id,
            "so_number": order.order_number,
            "customer_id": order.customer_id,
            "customer_name": customer.name if customer else "",
            "agency_id": order.agency_id,
            "agency_name": agency_name,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "total_amount": float(order.total_amount),
            "discount_percent": float(order.discount_percent) if hasattr(order, 'discount_percent') else 0,
            "discount_amount": float(order.discount_amount) if hasattr(order, 'discount_amount') else 0,
            "roundoff": float(order.roundoff) if hasattr(order, 'roundoff') else 0,
            "status": order.status,
            "items": [{
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name,
                "quantity": float(item.quantity),
                "free_quantity": float(getattr(item, 'free_quantity', 0)),
                "unit_price": float(item.unit_price),
                "gst_rate": float(item.gst_rate) if hasattr(item, 'gst_rate') else 0,
                "discount_percent": float(item.discount_percent) if hasattr(item, 'discount_percent') else 0,
                "discount_amount": float(item.discount_amount) if hasattr(item, 'discount_amount') else 0,
                "total_amount": float(item.total_price),
                "batch_number": getattr(item, 'batch_number', '')
            } for item, product in items]
        }
    
    return BaseResponse(
        success=True,
        message="Sales order retrieved successfully",
        data=order_data
    )

@router.post("/sales-orders/{order_id}/reverse", response_model=BaseResponse)
async def reverse_sales_order(order_id: int, reason_data: Dict[str, str], current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.sales_order_service import SalesOrderService
    
    sales_order_service = SalesOrderService()
    success = sales_order_service.reverse_order(order_id, reason_data.get('reason', ''))
    if not success:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    return BaseResponse(success=True, message="Sales order reversed successfully")

# Product Waste endpoints
@router.get("/product-wastes", response_model=PaginatedResponse)
async def get_product_wastes(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.product_waste_service import ProductWasteService
    
    product_waste_service = ProductWasteService()
    wastes = product_waste_service.get_all(page=pagination.page, page_size=pagination.per_page)
    total = product_waste_service.get_total_count()
    
    waste_data = [{
        "id": waste.id,
        "waste_number": waste.waste_number,
        "product_name": waste.product_name,
        "batch_number": waste.batch_number,
        "quantity": float(waste.quantity),
        "unit_cost": float(waste.unit_cost),
        "total_cost": float(waste.total_cost),
        "reason": waste.reason,
        "waste_date": waste.waste_date.isoformat() if waste.waste_date else None
    } for waste in wastes]
    
    return PaginatedResponse(
        success=True,
        message="Product wastes retrieved successfully",
        data=waste_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/product-wastes", response_model=BaseResponse)
async def create_product_waste(waste_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.product_waste_service import ProductWasteService
    
    product_waste_service = ProductWasteService()
    waste_id = product_waste_service.create(waste_data)
    return BaseResponse(
        success=True,
        message="Product waste recorded successfully",
        data={"id": waste_id}
    )

@router.delete("/product-wastes/{waste_id}", response_model=BaseResponse)
async def delete_product_waste(waste_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import ProductWaste
    
    with db_manager.get_session() as session:
        waste = session.query(ProductWaste).filter(ProductWaste.id == waste_id).first()
        if not waste:
            raise HTTPException(status_code=404, detail="Product waste not found")
        
        session.delete(waste)
        session.commit()
    
    return BaseResponse(success=True, message="Product waste deleted successfully")

# Export/Import endpoints
@router.get("/products/export-template", response_class=StreamingResponse)
async def export_products_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "code", "category", "unit", "price", "gst_percentage", "tags", "composition", "hsn_code", "schedule", "manufacturer"])
    writer.writerow(["Paracetamol 500mg", "PAR500", "Pharmacy", "Tablet", "25.50", "12.0", "#fever #pain", "Paracetamol 500mg", "30049099", "OTC", "ABC Pharma"])
    writer.writerow(["Vitamin C Tablets", "VITC100", "Nutrition & Supplements", "Tablet", "150.00", "18.0", "#vitamin #immunity", "Ascorbic Acid 100mg", "21069090", "OTC", "XYZ Health"])
    writer.writerow(["Cough Syrup", "COUGH250", "Pharmacy", "Bottle", "85.00", "12.0", "#cough #cold", "Dextromethorphan 15mg", "30049099", "Schedule H", "MediCorp"])
    
    content = output.getvalue()
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=products_import_template.csv"}
    )

@router.get("/units/export-template")
async def export_units_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "symbol", "is_active"])
    writer.writerow(["Kilogram", "kg", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=units_template.csv"}
    )

@router.post("/units/import", response_model=BaseResponse)
async def import_units(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Unit
    
    imported_count = 0
    with db_manager.get_session() as session:
        for row in csv_data:
            try:
                # Skip header rows - check if name field contains header-like values
                name_value = row.get("name", "").strip().lower()
                if name_value in ["name", "unit name", "unit"] or not name_value:
                    continue
                
                unit = Unit(
                    name=row["name"],
                    symbol=row["symbol"],
                    is_active=row["is_active"].lower() == "true"
                )
                session.add(unit)
                imported_count += 1
            except Exception as e:
                print(f"Error importing unit: {e}")
                continue
        session.commit()
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} units successfully"
    )

@router.get("/categories/export-template")
async def export_categories_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "parent_id", "description", "is_active"])
    writer.writerow(["Electronics", "", "Electronic products", "true"])
    writer.writerow(["Mobile Phones", "1", "Mobile phone category", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=categories_template.csv"}
    )

@router.post("/categories/import", response_model=BaseResponse)
async def import_categories(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Category
    
    imported_count = 0
    error_count = 0
    errors = []
    batch_size = 100
    categories_batch = []
    
    with db_manager.get_session() as session:
        for row_num, row in enumerate(csv_data, start=2):
            try:
                # Skip header rows
                name_value = row.get("name", "").strip()
                if not name_value or name_value.lower() in ["name", "category name", "category"]:
                    continue
                
                # Validate required fields
                if not row.get("is_active"):
                    errors.append(f"Row {row_num}: Missing is_active field")
                    error_count += 1
                    continue
                
                parent_id = None
                if row.get("parent_id") and row["parent_id"].strip():
                    try:
                        parent_id = int(row["parent_id"])
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid parent_id value")
                        error_count += 1
                        continue
                
                category = Category(
                    name=name_value,
                    parent_id=parent_id,
                    description=row.get("description", "").strip(),
                    tenant_id=current_user["tenant_id"],
                    is_active=row["is_active"].lower() == "true",
                    created_by=current_user["username"]
                )
                categories_batch.append(category)
                
                # Process batch
                if len(categories_batch) >= batch_size:
                    session.add_all(categories_batch)
                    session.flush()
                    imported_count += len(categories_batch)
                    categories_batch = []
                    
            except Exception as e:
                error_count += 1
                errors.append(f"Row {row_num}: {str(e)}")
        
        # Process remaining batch
        if categories_batch:
            session.add_all(categories_batch)
            session.flush()
            imported_count += len(categories_batch)
        
        session.commit()
    
    message = f"Import completed: {imported_count} categories imported"
    if error_count > 0:
        message += f", {error_count} errors"
        if errors:
            message += f". First few errors: {'; '.join(errors[:3])}"
    
    return BaseResponse(
        success=True,
        message=message
    )

@router.post("/products/import", response_model=BaseResponse)
async def import_products(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Category, Unit
    from core.shared.utils.session_manager import session_manager
    
    product_service = ProductService()
    imported_count = 0
    errors = []
    
    for row_num, row in enumerate(csv_data, start=2):
        try:
            name = str(row.get('name', '')).strip()
            category_name = str(row.get('category', '')).strip()
            unit_name = str(row.get('unit', '')).strip()
            price = row.get('price', '')
            
            if not name or not category_name or not unit_name or not price:
                errors.append(f"Row {row_num}: Missing required fields")
                continue
            
            # Find category and unit by name
            with db_manager.get_session() as session:
                tenant_id = session_manager.get_current_tenant_id()
                category = session.query(Category).filter(
                    Category.name == category_name,
                    Category.tenant_id == tenant_id
                ).first()
                
                if not category:
                    errors.append(f"Row {row_num}: Category '{category_name}' not found")
                    continue
                
                unit = session.query(Unit).filter(
                    Unit.name == unit_name
                ).first()
                
                if not unit:
                    errors.append(f"Row {row_num}: Unit '{unit_name}' not found")
                    continue
                
                product_data = {
                    'name': name,
                    'code': str(row.get('code', '')).strip(),
                    'category_id': category.id,
                    'unit_id': unit.id,
                    'price': float(price),
                    'gst_percentage': float(row.get('gst_percentage', 0)),
                    'tags': str(row.get('tags', '')).strip(),
                    'composition': str(row.get('composition', '')).strip(),
                    'hsn_code': str(row.get('hsn_code', '')).strip(),
                    'schedule': str(row.get('schedule', 'OTC')).strip(),
                    'manufacturer': str(row.get('manufacturer', '')).strip()
                }
                
                product_service.create(product_data)
                imported_count += 1
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
            continue
    
    message = f"Imported {imported_count} products successfully"
    if errors:
        message += f". {len(errors)} errors occurred"
    
    return BaseResponse(
        success=True,
        message=message
    )

@router.get("/customers/export-template")
async def export_customers_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "phone", "email", "age", "address", "tax_id", "is_active"])
    writer.writerow(["John Customer", "123-456-7890", "john@customer.com", "30", "123 Main St", "TAX001", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customers_template.csv"}
    )

@router.post("/customers/import", response_model=BaseResponse)
async def import_customers(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    customer_service = CustomerService()
    imported_count = 0
    
    for row in csv_data:
        try:
            customer_data = {
                "name": row["name"],
                "phone": row["phone"],
                "email": row.get("email", ""),
                "address": row.get("address", ""),
                "tax_id": row.get("tax_id", ""),
                "is_active": row["is_active"].lower() == "true"
            }
            
            # Add age if present
            if "age" in row and row["age"].strip():
                customer_data["age"] = int(row["age"])
            
            customer_service.create(customer_data)
            imported_count += 1
        except Exception:
            continue
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} customers successfully"
    )

@router.get("/suppliers/export-template")
async def export_suppliers_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "phone", "email", "tax_id", "contact_person", "address", "is_active"])
    writer.writerow(["ABC Supplier", "123-456-7890", "abc@supplier.com", "TAX001", "John Doe", "456 Supply St", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=suppliers_template.csv"}
    )

@router.post("/suppliers/import", response_model=BaseResponse)
async def import_suppliers(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    supplier_service = SupplierService()
    imported_count = 0
    
    for row in csv_data:
        try:
            supplier_data = {
                "name": row["name"],
                "phone": row["phone"],
                "email": row.get("email", ""),
                "tax_id": row.get("tax_id", ""),
                "contact_person": row.get("contact_person", ""),
                "address": row.get("address", ""),
                "is_active": row["is_active"].lower() == "true"
            }
            
            supplier_service.create(supplier_data)
            imported_count += 1
        except Exception:
            continue
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} suppliers successfully"
    )



@router.get("/stock-meter/export-template")
async def export_stock_meter_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["product_id", "quantity", "unit_price", "location"])
    writer.writerow(["1", "100", "10.50", "Warehouse A"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=stock_meter_template.csv"}
    )

@router.post("/stock-meter/import", response_model=BaseResponse)
async def import_stock_meter(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import StockMeter
    
    imported_count = 0
    with db_manager.get_session() as session:
        for row in csv_data:
            try:
                stock = StockMeter(
                    product_id=int(row["product_id"]),
                    quantity=int(row["quantity"]),
                    unit_price=float(row["unit_price"]),
                    location=row["location"]
                )
                session.add(stock)
                imported_count += 1
            except Exception:
                continue
        session.commit()
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} stock records successfully"
    )

# Stock Meter Summary endpoint
@router.get("/stock-meter-summary", response_model=BaseResponse)
async def get_stock_meter_summary(product_id: int = None, current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.stock_summary_service import StockSummaryService
    
    service = StockSummaryService()
    summary_data = service.get_stock_meter_summary(product_id)
    
    return BaseResponse(
        success=True,
        message="Stock meter summary retrieved successfully",
        data=summary_data
    )

# Stock Summary endpoint
@router.get("/stock-summary", response_model=BaseResponse)
async def get_stock_summary(product_id: int = None, current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.stock_summary_service import StockSummaryService
    
    service = StockSummaryService()
    summary_data = service.get_stock_summary(product_id)
    
    return BaseResponse(
        success=True,
        message="Stock summary retrieved successfully",
        data=summary_data
    )

# Stock Details endpoint
@router.get("/stock-details", response_model=PaginatedResponse)
async def get_stock_details(product_id: int = None, pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.stock_summary_service import StockSummaryService
    
    service = StockSummaryService()
    stock_data, total = service.get_stock_details_with_status(
        product_id=product_id,
        page=pagination.page,
        per_page=pagination.per_page,
        search=pagination.search
    )
    
    return PaginatedResponse(
        success=True,
        message="Stock details retrieved successfully",
        data=stock_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

# Stock Tracking Summary endpoint
@router.get("/stock-tracking-summary", response_model=BaseResponse)
async def get_stock_tracking_summary(
    product_id: int = None,
    movement_type: str = None,
    reference_type: str = None,
    from_date: str = None,
    to_date: str = None,
    current_user: dict = Depends(get_current_user)
):
    from modules.inventory_module.services.stock_summary_service import StockSummaryService
    
    service = StockSummaryService()
    summary_data = service.get_stock_tracking_summary(
        product_id=product_id,
        movement_type=movement_type,
        reference_type=reference_type,
        from_date=from_date,
        to_date=to_date
    )
    
    return BaseResponse(
        success=True,
        message="Stock tracking summary retrieved successfully",
        data=summary_data
    )

# Stock Movements endpoint
@router.get("/stock-movements", response_model=PaginatedResponse)
async def get_stock_movements(
    product_id: int = None,
    movement_type: str = None,
    reference_type: str = None,
    from_date: str = None,
    to_date: str = None,
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.inventory_module.models.stock_entities import StockTransaction
    from modules.inventory_module.models.entities import Product
    from sqlalchemy.orm import joinedload
    from sqlalchemy import and_, func
    from datetime import datetime
    from core.shared.utils.session_manager import session_manager
    
    with db_manager.get_session() as session:
        query = session.query(StockTransaction).options(joinedload(StockTransaction.product)).join(Product)
        
        # Apply tenant filter
        tenant_id = session_manager.get_current_tenant_id()
        if tenant_id:
            query = query.filter(StockTransaction.tenant_id == tenant_id)
        
        # Apply filters
        if product_id:
            query = query.filter(StockTransaction.product_id == product_id)
        
        if movement_type:
            if movement_type == 'in':
                query = query.filter(StockTransaction.transaction_type == 'IN')
            elif movement_type == 'out':
                query = query.filter(StockTransaction.transaction_type == 'OUT')
        
        if reference_type:
            source_mapping = {
                'Purchase Order': 'PURCHASE',
                'Sales Order': 'SALES',
                'Product Waste': 'WASTE',
                'Stock Adjustment': 'ADJUSTMENT'
            }
            if reference_type in source_mapping:
                query = query.filter(StockTransaction.transaction_source == source_mapping[reference_type])
        
        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                query = query.filter(StockTransaction.transaction_date >= from_dt)
            except ValueError:
                pass
        
        if to_date:
            try:
                to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                query = query.filter(StockTransaction.transaction_date <= to_dt)
            except ValueError:
                pass
        
        # Apply search filter
        if pagination.search:
            query = query.filter(or_(
                Product.name.ilike(f"%{pagination.search}%"),
                StockTransaction.reference_number.ilike(f"%{pagination.search}%"),
                StockTransaction.batch_number.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        transactions = query.order_by(StockTransaction.transaction_date.desc()).offset(pagination.offset).limit(pagination.per_page).all()
        
        # Calculate running balance for each transaction
        movement_data = []
        for transaction in transactions:
            # Map transaction source to reference type
            reference_type_map = {
                'PURCHASE': 'Purchase Order',
                'SALES': 'Sales Order',
                'WASTE': 'Product Waste',
                'ADJUSTMENT': 'Stock Adjustment',
                'SALES_REVERSAL': 'Sales Reversal',
                'PURCHASE_REVERSAL': 'Purchase Reversal'
            }
            
            movement_data.append({
                "id": transaction.id,
                "product_id": transaction.product_id,
                "product_name": transaction.product.name,
                "batch_number": transaction.batch_number or "",
                "movement_type": transaction.transaction_type.lower(),
                "quantity": float(transaction.quantity),
                "reference_type": reference_type_map.get(transaction.transaction_source, transaction.transaction_source),
                "reference_number": transaction.reference_number,
                "movement_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                "notes": f"{transaction.transaction_source} transaction",
                "unit_price": float(transaction.unit_price or 0)
            })
    
    return PaginatedResponse(
        success=True,
        message="Stock movements retrieved successfully",
        data=movement_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )