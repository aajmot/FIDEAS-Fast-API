from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

from core.database.connection import db_manager
from api.v1.routers import auth, admin, inventory, account, clinic, care, diagnostic, agency_commission, order_commission, account_extensions, dashboard, comparative_reports, gst_reports, inventory_extensions, batch_management, currency, reconciliation, notifications, invoice, warehouse, fixed_assets, approvals, gst_compliance
from api.v2.routers import admin as admin_v2
from api.middleware.auth_middleware import get_current_user
from api.version_manager import version_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_manager._initialize_database()
    yield

app = FastAPI(
    title="FIDEAS API",
    description="Enterprise Management System API",
    version="1.0.0",
    lifespan=lifespan,
    servers=[
        {"url": "/", "description": "Default Server"}
    ],
    swagger_ui_parameters={"docExpansion": "none"}
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# API v1 routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication v1"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin v1"], dependencies=[Depends(get_current_user)])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory v1"], dependencies=[Depends(get_current_user)])
app.include_router(account.router, prefix="/api/v1/account", tags=["Account v1"], dependencies=[Depends(get_current_user)])
app.include_router(account_extensions.router, prefix="/api/v1/account", tags=["Account Extensions v1"], dependencies=[Depends(get_current_user)])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard v1"], dependencies=[Depends(get_current_user)])
app.include_router(clinic.router, prefix="/api/v1/clinic", tags=["Clinic v1"], dependencies=[Depends(get_current_user)])
app.include_router(care.router, prefix="/api/v1/care", tags=["Care v1"], dependencies=[Depends(get_current_user)])
app.include_router(diagnostic.router, prefix="/api/v1/diagnostic", tags=["Diagnostic v1"], dependencies=[Depends(get_current_user)])
app.include_router(agency_commission.router, prefix="/api/v1/admin", tags=["Admin v1"], dependencies=[Depends(get_current_user)])
app.include_router(order_commission.router, prefix="/api/v1/admin", tags=["Admin v1"], dependencies=[Depends(get_current_user)])
app.include_router(comparative_reports.router, prefix="/api/v1/comparative-reports", tags=["Comparative Reports v1"], dependencies=[Depends(get_current_user)])
app.include_router(gst_reports.router, prefix="/api/v1/gst", tags=["GST Reports v1"], dependencies=[Depends(get_current_user)])
app.include_router(inventory_extensions.router, prefix="/api/v1/inventory", tags=["Inventory Extensions v1"], dependencies=[Depends(get_current_user)])
app.include_router(batch_management.router, prefix="/api/v1/batch", tags=["Batch Management v1"], dependencies=[Depends(get_current_user)])
app.include_router(currency.router, prefix="/api/v1/currency", tags=["Multi-Currency v1"], dependencies=[Depends(get_current_user)])
app.include_router(reconciliation.router, prefix="/api/v1/reconciliation", tags=["Reconciliation v1"], dependencies=[Depends(get_current_user)])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications v1"], dependencies=[Depends(get_current_user)])
app.include_router(invoice.router, prefix="/api/v1/invoice", tags=["Invoice v1"], dependencies=[Depends(get_current_user)])
app.include_router(warehouse.router, prefix="/api/v1/warehouse", tags=["Warehouse v1"], dependencies=[Depends(get_current_user)])
app.include_router(fixed_assets.router, prefix="/api/v1/fixed-assets", tags=["Fixed Assets v1"], dependencies=[Depends(get_current_user)])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["Approvals v1"], dependencies=[Depends(get_current_user)])
app.include_router(gst_compliance.router, prefix="/api/v1/gst", tags=["GST Compliance v1"], dependencies=[Depends(get_current_user)])

# API v2 routes
app.include_router(admin_v2.router, prefix="/api/v2/admin", tags=["Admin v2"], dependencies=[Depends(get_current_user)])

# Register version management routes
version_manager.register_version_routes(app)

@app.get("/")
async def root():
    return {
        "message": "FIDEAS API is running",
        "version": "1.0.0",
        "api_version": version_manager.default_version,
        "available_versions": version_manager.get_available_versions(),
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": version_manager.default_version}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)