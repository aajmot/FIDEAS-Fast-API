from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from api.v1.routers.dashboards_routes import dashboard_route
from api.v1.routers.inventory_routes import batch_management_route, order_commission_route, warehouse_route
from api.v1.routers.notification_routes import notifications_route
from api.v1.routers.inventory_routes import (
    categories_route,
    customers_route,
    products_route,
    purchase_invoices_route,
    purchase_orders_route,
    sales_invoices_route,
    sales_orders_route,
    stocks_route,
    suppliers_route,
    units_route,
    waste_products_route,
    stock_adjustments_route,
    stock_transfers_route,
)

load_dotenv()

from api.v1.routers.admin_routes import (
    currency,
    financial_years_route,
    user_role_mappings_route,
    users_route,
    menus_route,
    roles_route,
    tenant_route,
    legal_entities_route,
    agencies_route,
    role_menu_mappings_route,
    transaction_templates_route,
    account_configurations_route,
    branches_route,
)
from api.v1.routers.people_routes import departments_route, employees_route
from api.v1.routers.account_routes import (
    comparative_reports_route,
    reconciliation_route,
    vouchers_route,
    payments_route,
    ledger_route,
    journals_route,
    account_groups_route,
    account_masters_route,
    account_configuration_keys_route,
    taxes_route,
    bank_reconciliation_route,
    recurring_vouchers_route,
    voucher_series_route,
    cost_centers_route,
    budgets_route,
    audit_route,
    gst_route,
    reports_route,
    payment_terms_route,
    account_types_route,
)
from api.v1.routers.account_routes import (
    contra_route,
    credit_notes_route,
    debit_notes_route,
    aging_route,
    tds_route,
)
from core.database.connection import db_manager
import types
from fastapi import APIRouter

# Import models to ensure they're registered with SQLAlchemy
from modules.account_module.models.bank_account_entity import BankAccount
from modules.people_module.models.department_entity import Department
from modules.people_module.models.employee_entity import Employee

# Import commonly-used routers directly; provide safe fallbacks for
# optional/legacy modules so the app can still start during the refactor.
try:
    from api.v1.routers.admin_routes import agency_commission_route, approvals_route
except Exception:
    agency_commission_route = types.SimpleNamespace(router=APIRouter())
    approvals_route = types.SimpleNamespace(router=APIRouter())

try:
    from api.v1.routers import auth
except Exception:
    auth = types.SimpleNamespace(router=APIRouter())

try:
    from api.v1.routers import dashboard
except Exception:
    dashboard = types.SimpleNamespace(router=APIRouter())

try:
    from api.v1.routers import notifications
except Exception:
    notifications = types.SimpleNamespace(router=APIRouter())

try:
    # explicit import for fixed assets routes in asset_routes package
    from api.v1.routers.asset_routes import fixed_assets_route as fixed_assets
except Exception:
    fixed_assets = types.SimpleNamespace(router=APIRouter())

try:
    # import health routes (grouped under health_routes package)
    from api.v1.routers.health_routes import (
        appointments_route,
        billing_masters_route,
        doctors_route,
        invoices_route as health_invoices_route,
        lab_technicians_route,
        medical_records_route,
        patients_route,
        prescriptions_route,
        sample_collections_route,
        testcategories_route,
        testorders_route,
        testpanels_route,
        testresults_route,
        tests_route,
    )
except Exception:
    appointments_route = types.SimpleNamespace(router=APIRouter())
    billing_masters_route = types.SimpleNamespace(router=APIRouter())
    doctors_route = types.SimpleNamespace(router=APIRouter())
    health_invoices_route = types.SimpleNamespace(router=APIRouter())
    lab_technicians_route = types.SimpleNamespace(router=APIRouter())
    medical_records_route = types.SimpleNamespace(router=APIRouter())
    patients_route = types.SimpleNamespace(router=APIRouter())
    prescriptions_route = types.SimpleNamespace(router=APIRouter())
    sample_collections_route = types.SimpleNamespace(router=APIRouter())
    testcategories_route = types.SimpleNamespace(router=APIRouter())
    testorders_route = types.SimpleNamespace(router=APIRouter())
    testpanels_route = types.SimpleNamespace(router=APIRouter())
    testresults_route = types.SimpleNamespace(router=APIRouter())
    tests_route = types.SimpleNamespace(router=APIRouter())

def _load_optional(name, module_path="api.v1.routers"):
    try:
        module = __import__(module_path, fromlist=[name])
        return getattr(module, name)
    except Exception:
        return types.SimpleNamespace(router=APIRouter())

gst_compliance_route = _load_optional('gst_compliance_route')
gst_reports_route = _load_optional('gst_reports_route')
inventory = _load_optional('inventory')
account = _load_optional('account')
account_extensions = _load_optional('account_extensions')
inventory_extensions = _load_optional('inventory_extensions')
invoice = _load_optional('invoice')
from api.v2.routers.admin_routes import user_route as admin_v2
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
# CORS middleware
# Configure allowed origins via ALLOWED_ORIGINS environment variable (comma-separated).
# If ALLOWED_ORIGINS is '*' we must NOT set allow_credentials=True because browsers
# block '*' with credentials. When specific origins are provided, credentials are allowed.
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_env and allowed_origins_env.strip() != "*":
    allow_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    allow_credentials = True
else:
    allow_origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"]
)

#region v1 -all routes

#region auth routes
# tags follow pattern '<module>-<entity> v1'
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth-authentication v1"])
#endregion auth routes

#region admin routes
# Admin routes: tags use 'admin-<entity> v1'
app.include_router(users_route.router, prefix="/api/v1/admin", tags=["admin-users v1"], dependencies=[Depends(get_current_user)])
app.include_router(roles_route.router, prefix="/api/v1/admin", tags=["admin-roles v1"], dependencies=[Depends(get_current_user)])
app.include_router(user_role_mappings_route.router, prefix="/api/v1/admin", tags=["admin-user-role-mappings v1"], dependencies=[Depends(get_current_user)])
app.include_router(menus_route.router, prefix="/api/v1/admin", tags=["admin-menus v1"], dependencies=[Depends(get_current_user)])
app.include_router(approvals_route.router, prefix="/api/v1/admin", tags=["admin-approvals v1"], dependencies=[Depends(get_current_user)])
app.include_router(tenant_route.router, prefix="/api/v1/admin", tags=["admin-tenant v1"], dependencies=[Depends(get_current_user)])
app.include_router(currency.router, prefix="/api/v1/admin", tags=["admin-currencies v1"], dependencies=[Depends(get_current_user)])
app.include_router(account_configuration_keys_route.router, prefix="/api/v1/admin", tags=["admin-account-configuration-keys v1"], dependencies=[Depends(get_current_user)])
app.include_router(account_configurations_route.router, prefix="/api/v1/admin", tags=["admin-account-configurations v1"], dependencies=[Depends(get_current_user)])
app.include_router(transaction_templates_route.router, prefix="/api/v1/admin", tags=["admin-transaction-templates v1"], dependencies=[Depends(get_current_user)])
app.include_router(role_menu_mappings_route.router, prefix="/api/v1/admin", tags=["admin-role-menu-mappings v1"], dependencies=[Depends(get_current_user)])
app.include_router(legal_entities_route.router, prefix="/api/v1/admin", tags=["admin-legal-entities v1"], dependencies=[Depends(get_current_user)])
app.include_router(financial_years_route.router, prefix="/api/v1/admin", tags=["admin-financial-years v1"], dependencies=[Depends(get_current_user)])
app.include_router(agencies_route.router, prefix="/api/v1/admin", tags=["admin-agencies v1"], dependencies=[Depends(get_current_user)])
app.include_router(agency_commission_route.router, prefix="/api/v1/admin", tags=["admin-agency-commissions v1"], dependencies=[Depends(get_current_user)])
app.include_router(branches_route.router, prefix="/api/v1/admin", tags=["admin-branches v1"], dependencies=[Depends(get_current_user)])

#endregion admin routes

#region inventory routes

app.include_router(batch_management_route.router, prefix="/api/v1/batch", tags=["inventory-batch v1"], dependencies=[Depends(get_current_user)])
app.include_router(order_commission_route.router, prefix="/api/v1/inventory", tags=["inventory-order-commissions v1"], dependencies=[Depends(get_current_user)])
app.include_router(categories_route.router, prefix="/api/v1/inventory", tags=["inventory-categories v1"], dependencies=[Depends(get_current_user)])
app.include_router(products_route.router, prefix="/api/v1/inventory", tags=["inventory-products v1"], dependencies=[Depends(get_current_user)])
app.include_router(customers_route.router, prefix="/api/v1/inventory", tags=["inventory-customers v1"], dependencies=[Depends(get_current_user)])
app.include_router(suppliers_route.router, prefix="/api/v1/inventory", tags=["inventory-suppliers v1"], dependencies=[Depends(get_current_user)])
app.include_router(units_route.router, prefix="/api/v1/inventory", tags=["inventory-units v1"], dependencies=[Depends(get_current_user)])
app.include_router(purchase_orders_route.router, prefix="/api/v1/inventory", tags=["inventory-purchase-orders v1"], dependencies=[Depends(get_current_user)])
app.include_router(sales_orders_route.router, prefix="/api/v1/inventory", tags=["inventory-sales-orders v1"], dependencies=[Depends(get_current_user)])
app.include_router(purchase_invoices_route.router, prefix="/api/v1/inventory", tags=["inventory-purchase-invoices v1"], dependencies=[Depends(get_current_user)])
app.include_router(sales_invoices_route.router, prefix="/api/v1/inventory", tags=["inventory-sales-invoices v1"], dependencies=[Depends(get_current_user)])
app.include_router(stocks_route.router, prefix="/api/v1/inventory", tags=["inventory-stocks v1"], dependencies=[Depends(get_current_user)])
app.include_router(waste_products_route.router, prefix="/api/v1/inventory", tags=["inventory-waste-products v1"], dependencies=[Depends(get_current_user)])
app.include_router(stock_adjustments_route.router, prefix="/api/v1/inventory", tags=["inventory-stock-adjustments v1"], dependencies=[Depends(get_current_user)])
app.include_router(stock_transfers_route.router, prefix="/api/v1/inventory", tags=["inventory-stock-transfers v1"], dependencies=[Depends(get_current_user)])
app.include_router(invoice.router, prefix="/api/v1/invoice", tags=["invoices v1"], dependencies=[Depends(get_current_user)])
app.include_router(warehouse_route.router, prefix="/api/v1/inventory", tags=["inventory-warehouse v1"], dependencies=[Depends(get_current_user)])
app.include_router(inventory_extensions.router, prefix="/api/v1/inventory", tags=["inventory-extensions v1"], dependencies=[Depends(get_current_user)])


#endregion inventory routes

#region account routes
app.include_router(vouchers_route.router, prefix="/api/v1/account", tags=["account-vouchers v1"], dependencies=[Depends(get_current_user)])
app.include_router(payments_route.router, prefix="/api/v1/account", tags=["account-payments v1"], dependencies=[Depends(get_current_user)])
app.include_router(ledger_route.router, prefix="/api/v1/account", tags=["account-ledger v1"], dependencies=[Depends(get_current_user)])
app.include_router(journals_route.router, prefix="/api/v1/account", tags=["account-journals v1"], dependencies=[Depends(get_current_user)])
app.include_router(account_groups_route.router, prefix="/api/v1/account", tags=["account-account-groups v1"], dependencies=[Depends(get_current_user)])
app.include_router(account_masters_route.router, prefix="/api/v1/account", tags=["account-account-masters v1"], dependencies=[Depends(get_current_user)])
app.include_router(taxes_route.router, prefix="/api/v1/account", tags=["account-taxes v1"], dependencies=[Depends(get_current_user)])
app.include_router(bank_reconciliation_route.router, prefix="/api/v1/account", tags=["account-bank-reconciliations v1"], dependencies=[Depends(get_current_user)])
app.include_router(reconciliation_route.router, prefix="/api/v1/account", tags=["account-reconciliation v1"], dependencies=[Depends(get_current_user)])
app.include_router(recurring_vouchers_route.router, prefix="/api/v1/account", tags=["account-recurring-vouchers v1"], dependencies=[Depends(get_current_user)])
app.include_router(voucher_series_route.router, prefix="/api/v1/account", tags=["account-voucher-series v1"], dependencies=[Depends(get_current_user)])
app.include_router(reports_route.router, prefix="/api/v1/account", tags=["account-reports v1"], dependencies=[Depends(get_current_user)])
app.include_router(cost_centers_route.router, prefix="/api/v1/account", tags=["account-cost-centers v1"], dependencies=[Depends(get_current_user)])
app.include_router(budgets_route.router, prefix="/api/v1/account", tags=["account-budgets v1"], dependencies=[Depends(get_current_user)])
app.include_router(audit_route.router, prefix="/api/v1/account", tags=["account-audit v1"], dependencies=[Depends(get_current_user)])
app.include_router(gst_route.router, prefix="/api/v1/account", tags=["account-gst v1"], dependencies=[Depends(get_current_user)])
# remaining account routes (already follow the pattern)
app.include_router(contra_route.router, prefix="/api/v1/account", tags=["account-contra v1"], dependencies=[Depends(get_current_user)])
app.include_router(credit_notes_route.router, prefix="/api/v1/account", tags=["account-credit-notes v1"], dependencies=[Depends(get_current_user)])
app.include_router(debit_notes_route.router, prefix="/api/v1/account", tags=["account-debit-notes v1"], dependencies=[Depends(get_current_user)])
app.include_router(aging_route.router, prefix="/api/v1/account", tags=["account-aging v1"], dependencies=[Depends(get_current_user)])
app.include_router(tds_route.router, prefix="/api/v1/account", tags=["account-tds v1"], dependencies=[Depends(get_current_user)])
app.include_router(payment_terms_route.router, prefix="/api/v1/account", tags=["account-payment-terms v1"], dependencies=[Depends(get_current_user)])
app.include_router(comparative_reports_route.router, prefix="/api/v1/account", tags=["account-comparative-reports v1"], dependencies=[Depends(get_current_user)])
app.include_router(gst_reports_route.router, prefix="/api/v1/account", tags=["account-gst-reports v1"], dependencies=[Depends(get_current_user)])
app.include_router(gst_compliance_route.router, prefix="/api/v1/account", tags=["account-gst-compliance v1"], dependencies=[Depends(get_current_user)])
app.include_router(account_types_route.router, prefix="/api/v1/account", tags=["account-account-types v1"], dependencies=[Depends(get_current_user)])

#endregion account routes

#region dashboard routes
app.include_router(dashboard_route.router, prefix="/api/v1/dashboard", tags=["dashboard-dashboard v1"], dependencies=[Depends(get_current_user)])
#endregion dashboard routes

#region health routes
app.include_router(appointments_route.router, prefix="/api/v1/health", tags=["health-appointments v1"], dependencies=[Depends(get_current_user)])
app.include_router(billing_masters_route.router, prefix="/api/v1/health", tags=["health-billing v1"], dependencies=[Depends(get_current_user)])
app.include_router(doctors_route.router, prefix="/api/v1/health", tags=["health-doctors v1"], dependencies=[Depends(get_current_user)])
app.include_router(health_invoices_route.router, prefix="/api/v1/health", tags=["health-invoices v1"], dependencies=[Depends(get_current_user)])
app.include_router(lab_technicians_route.router, prefix="/api/v1/health", tags=["health-lab-technicians v1"], dependencies=[Depends(get_current_user)])
app.include_router(medical_records_route.router, prefix="/api/v1/health", tags=["health-medical-records v1"], dependencies=[Depends(get_current_user)])
app.include_router(patients_route.router, prefix="/api/v1/health", tags=["health-patients v1"], dependencies=[Depends(get_current_user)])
app.include_router(prescriptions_route.router, prefix="/api/v1/health", tags=["health-prescriptions v1"], dependencies=[Depends(get_current_user)])
app.include_router(sample_collections_route.router, prefix="/api/v1/health", tags=["health-sample-collections v1"], dependencies=[Depends(get_current_user)])
app.include_router(testcategories_route.router, prefix="/api/v1/health", tags=["health-test-categories v1"], dependencies=[Depends(get_current_user)])
app.include_router(testorders_route.router, prefix="/api/v1/health", tags=["health-test-orders v1"], dependencies=[Depends(get_current_user)])
app.include_router(testpanels_route.router, prefix="/api/v1/health", tags=["health-test-panels v1"], dependencies=[Depends(get_current_user)])
app.include_router(testresults_route.router, prefix="/api/v1/health", tags=["health-test-results v1"], dependencies=[Depends(get_current_user)])
app.include_router(tests_route.router, prefix="/api/v1/health", tags=["health-tests v1"], dependencies=[Depends(get_current_user)])
#endregion health routes

#region notification routes
app.include_router(notifications_route.router, prefix="/api/v1/notifications", tags=["notification-notifications v1"], dependencies=[Depends(get_current_user)])

#endregion notification routes


#region asset routes
app.include_router(fixed_assets.router, prefix="/api/v1/asset", tags=["asset-fixed-assets v1"], dependencies=[Depends(get_current_user)])

#endregion asset routes

#region people routes
app.include_router(departments_route.router, prefix="/api/v1/people", tags=["people-departments v1"], dependencies=[Depends(get_current_user)])
app.include_router(employees_route.router, prefix="/api/v1/people", tags=["people-employees v1"], dependencies=[Depends(get_current_user)])

#endregion people routes



#endregion -all routes


# API v1 routes







# API v2 routes
app.include_router(admin_v2.router, prefix="/api/v2/admin", tags=["admin-users v2"], dependencies=[Depends(get_current_user)])

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