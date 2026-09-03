"""BhoomiSetu FastAPI application — entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import check_db_connection

settings = get_settings()

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="BhoomiSetu API",
    description=(
        "Land acquisition & compensation management platform "
        "for Indian infrastructure projects."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
# Uncomment each router as it is implemented:
# from app.routers import auth, projects, parcels, gis, dashboard
# from app.routers import analytics, documents, alerts, admin, reports
# app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["Auth"])
# app.include_router(projects.router,   prefix="/api/v1/projects",   tags=["Projects"])
# app.include_router(parcels.router,    prefix="/api/v1/parcels",    tags=["Parcels"])
# app.include_router(gis.router,        prefix="/api/v1/gis",        tags=["GIS"])
# app.include_router(dashboard.router,  prefix="/api/v1/dashboard",  tags=["Dashboard"])
# app.include_router(analytics.router,  prefix="/api/v1/analytics",  tags=["Analytics"])
# app.include_router(documents.router,  prefix="/api/v1/documents",  tags=["Documents"])
# app.include_router(alerts.router,     prefix="/api/v1/alerts",     tags=["Alerts"])
# app.include_router(admin.router,      prefix="/api/v1/admin",      tags=["Admin"])
# app.include_router(reports.router,    prefix="/api/v1/reports",    tags=["Reports"])


# ── System endpoints ──────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="Liveness probe")
async def health() -> dict:
    """Returns service status and database reachability."""
    db_ok = check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "version": app.version,
    }


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"message": "BhoomiSetu API — see /docs for the OpenAPI reference."}
