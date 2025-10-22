from fastapi import APIRouter
from app.api.v1.controllers.inventory.product_controller import router as product_router
from app.api.v1.controllers.inventory.category_controller import router as category_router
from app.api.v1.controllers.inventory.unit_controller import router as unit_router
from app.api.v1.controllers.inventory.customer_controller import router as customer_router
from app.api.v1.controllers.inventory.supplier_controller import router as supplier_router
from app.api.v1.controllers.inventory.invoice_controller import router as invoice_router

router = APIRouter()

# Include all inventory controllers
router.include_router(product_router, tags=["Inventory - Products"])
router.include_router(category_router, tags=["Inventory - Categories"])
router.include_router(unit_router, tags=["Inventory - Units"])
router.include_router(customer_router, tags=["Inventory - Customers"])
router.include_router(supplier_router, tags=["Inventory - Suppliers"])
router.include_router(invoice_router, tags=["Inventory - Invoices"])