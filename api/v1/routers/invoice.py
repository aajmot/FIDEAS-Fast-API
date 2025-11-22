"""
Invoice Routes Module
Aggregates both purchase and sales invoice routes under /api/v1/invoice prefix
"""
from fastapi import APIRouter
from api.v1.routers.inventory_routes import purchase_invoices_route, sales_invoices_route

router = APIRouter()

# Include purchase invoices routes
router.include_router(
    purchase_invoices_route.router,
    tags=["invoices"]
)

# Include sales invoices routes
router.include_router(
    sales_invoices_route.router,
    tags=["invoices"]
)
