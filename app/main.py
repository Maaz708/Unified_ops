# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import configure_logging
from app.core.config import settings
from app.api.routers import auth, workspaces, public_bookings, public_forms, inbox, analytics, health, forms, bookings, staff, inventory
from app.api.routers import owner_availability

# Ensure all ORM models are loaded so SQLAlchemy can resolve relationship names
import app.models  # noqa: F401


def create_app() -> FastAPI:
    configure_logging(level=settings.log_level if hasattr(settings, "log_level") else "INFO")
    app = FastAPI(
        title="Unified Operations Platform",
        version="0.1.0",
        debug=settings.debug,
    )

    # CORS: with credentials=True we must list origins explicitly (no "*")
    # Normalize to strings and strip trailing slash so they match browser Origin header
    def _norm(o):
        s = str(o).strip().rstrip("/")
        return s or None

    dev_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    raw = list(settings.cors_origins) if settings.cors_origins else []
    if settings.app_env == "development" and not raw:
        raw = dev_origins
    if settings.frontend_url:
        raw.append(settings.frontend_url)
    origins = list({_norm(o) for o in raw if _norm(o)})
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Routers
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(workspaces.router, prefix="/api/v1")
    app.include_router(staff.router, prefix="/api/v1")
    app.include_router(inventory.router, prefix="/api/v1")
    app.include_router(public_bookings.router, prefix="/api/v1")
    app.include_router(inbox.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(forms.router, prefix="/api/v1/workspaces")
    app.include_router(bookings.router, prefix="/api/v1/workspaces")
    app.include_router(public_forms.router, prefix="/api/v1")
    return app


app = create_app()
app.include_router(owner_availability.router)
app.include_router(public_forms.router) # Include the new router

@app.get("/")
def root():
    return {
        "service": "Unified Operations Platform",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
