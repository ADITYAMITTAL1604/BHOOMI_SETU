"""app.routers package."""

from app.routers import auth
from app.routers import projects
from app.routers import parcels
from app.routers import gis
from app.routers import dashboard
from app.routers import analytics
from app.routers import documents
from app.routers import alerts
from app.routers import admin
from app.routers import reports

__all__ = [
    "auth",
    "projects",
    "parcels",
    "gis",
    "dashboard",
    "analytics",
    "documents",
    "alerts",
    "admin",
    "reports",
]