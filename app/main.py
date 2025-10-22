from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.core.middleware.logging_middleware import LoggingMiddleware
from app.core.middleware.cors_middleware import setup_cors
from app.core.exceptions.error_handler import setup_exception_handlers
from app.db.base import init_db
from app.api.v1.routes import inventory_routes, accounting_routes, clinic_routes, diagnostics_routes, admin_routes
from app.api.v1.routes import warehouse_routes, notification_routes, report_routes
from app.api.public.auth_routes import router as auth_router
from app.api.public.health_routes import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Enterprise Management System API",
        version=settings.VERSION,
        debug=settings.DEBUG,
        swagger_ui_parameters={"docExpansion": "none"}
    )
    
    # Initialize database on startup
    @app.on_event("startup")
    async def startup_event():
        try:
            init_db()
        except Exception as e:
            print(f"Database initialization failed: {e}")
            # Continue without database - app will still start
    
    # Setup middleware
    app.add_middleware(LoggingMiddleware)
    setup_cors(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Public routes (no auth required)
    app.include_router(auth_router, prefix="/api/public/auth", tags=["Authentication"])
    app.include_router(health_router, prefix="/api/public", tags=["Health"])
    
    # V1 API routes
    app.include_router(inventory_routes.router, prefix="/api/v1/inventory")
    app.include_router(accounting_routes.router, prefix="/api/v1/account")
    app.include_router(clinic_routes.router, prefix="/api/v1/clinic")
    app.include_router(diagnostics_routes.router, prefix="/api/v1/diagnostics")
    app.include_router(admin_routes.router, prefix="/api/v1/admin")
    app.include_router(warehouse_routes.router, prefix="/api/v1/warehouse")
    app.include_router(notification_routes.router, prefix="/api/v1/notifications")
    app.include_router(report_routes.router, prefix="/api/v1/reports")
    
    return app


app = create_app()


@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.VERSION,
        "docs": "/docs"
    }