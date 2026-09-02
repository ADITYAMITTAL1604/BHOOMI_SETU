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

import logging
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    """Ensure all HTTPExceptions return a consistent JSON error envelope."""
    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status": exc.status_code,
            "status_code": exc.status_code,
        },
        headers=headers,
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Clean validation error responses across all CRUD APIs with polished frontend messages."""
    errors = exc.errors()

    # 1. Check for geometry/bbox/WKT validation errors -> 400 Bad Request
    for err in errors:
        msg = err.get("msg", "")
        loc_str = " ".join(str(x).lower() for x in err.get("loc", ()))
        msg_lower = msg.lower()
        if (
            any(k in loc_str for k in ("geometry", "bbox", "min_lon", "max_lon", "min_lat", "max_lat", "wkt", "geojson"))
            or any(k in msg_lower for k in ("geometry", "bounding box", "wkt", "geojson", "polygon", "vertices", "india"))
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "detail": msg,
                    "status": 400,
                    "status_code": 400,
                },
            )

    # 2. Format clean human-readable primary messages with edge-case clarity
    formatted_msgs = []
    for err in errors:
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        err_type = err.get("type", "")
        msg = err.get("msg", "Invalid value")
        
        # Improve edge-case messages for frontend display
        if "missing" in err_type or "value_error.missing" in err_type:
            friendly_msg = f"{loc}: This field is required and cannot be empty." if loc else "Required field is missing."
        elif "greater_than" in err_type or "value_error.number.not_gt" in err_type:
            friendly_msg = f"{loc}: Must be a positive number greater than 0." if loc else msg
        elif "less_than" in err_type or "value_error.number.not_le" in err_type:
            friendly_msg = f"{loc}: Value exceeds maximum permitted limit." if loc else msg
        elif "uuid" in err_type or "value_error.uuid" in err_type:
            friendly_msg = f"{loc}: Must be a valid UUID format." if loc else msg
        elif "string_too_long" in err_type:
            friendly_msg = f"{loc}: Input text exceeds maximum allowed length." if loc else msg
        elif "string_too_short" in err_type:
            friendly_msg = f"{loc}: Input text is too short." if loc else msg
        else:
            friendly_msg = f"{loc}: {msg}" if loc else msg
            
        formatted_msgs.append(friendly_msg)

    primary_msg = "; ".join(formatted_msgs) if formatted_msgs else "Validation error occurred."
    return JSONResponse(
        status_code=422,
        content={
            "detail": primary_msg,
            "message": primary_msg,
            "status": 422,
            "status_code": 422,
            "errors": errors,
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    """Catch-all for unhandled exceptions to return a clean 500 error envelope."""
    logger.exception("Unhandled server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "message": "An internal server error occurred. Please try again later.",
            "status": 500,
            "status_code": 500,
        },
    )

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Custom Middlewares ────────────────────────────────────────────────────────
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.request_size import RequestSizeLimitMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RateLimitMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.routers import (
    auth,
    projects,
    parcels,
    gis,
    dashboard,
    analytics,
    documents,
    alerts,
    compensation,
    rr,
    audit_log,
    search,
    admin,
    reports,
)

app.include_router(auth.router,          prefix="/api/v1/auth",         tags=["Auth"])
app.include_router(projects.router,      prefix="/api/v1/projects",     tags=["Projects"])
app.include_router(parcels.router,       prefix="/api/v1/parcels",      tags=["Parcels"])
app.include_router(gis.router,           prefix="/api/v1/gis",          tags=["GIS"])
app.include_router(dashboard.router,     prefix="/api/v1/dashboard",    tags=["Dashboard"])
app.include_router(analytics.router,     prefix="/api/v1/analytics",    tags=["Analytics"])
app.include_router(analytics.router,     prefix="/analytics",           tags=["Analytics"], include_in_schema=False)
app.include_router(documents.router,     prefix="/api/v1/documents",    tags=["Documents"])
app.include_router(alerts.router,        prefix="/api/v1/alerts",       tags=["Alerts"])
app.include_router(compensation.router,  prefix="/api/v1/compensation", tags=["Compensation"])
app.include_router(rr.router,            prefix="/api/v1/rr",           tags=["Rehabilitation & Resettlement"])
app.include_router(audit_log.router,     prefix="/api/v1/audit-log",    tags=["Audit Log"])
app.include_router(search.router,        prefix="/api/v1/search",       tags=["Search"])
app.include_router(admin.router,         prefix="/api/v1/admin",        tags=["Admin"])
app.include_router(reports.router,       prefix="/api/v1/reports",      tags=["Reports"])


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
