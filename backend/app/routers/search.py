"""FastAPI router for /search — global full-text search across projects and parcels."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_user_geographic_scope
from app.database import get_db
from app.models import Parcel, Project, User

router = APIRouter()


@router.get(
    "",
    summary="Global search across projects and parcels",
    response_model=dict,
)
def global_search(
    q: str = Query(..., min_length=2, description="Search query (min 2 characters)"),
    type: Optional[str] = Query(None, description="Filter to 'projects', 'parcels', or 'all' (default)"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Full-text search across projects and parcels with geographic scope enforcement.

    Projects: matches name, type, states, districts.
    Parcels: matches survey_number, owner_name, village, district.
    Results are grouped by entity type, max `limit` per group.
    """
    scope = get_user_geographic_scope(current_user)
    search_term = f"%{q.strip()}%"
    search_type = (type or "all").lower()

    projects = []
    parcels = []

    # ── Project search ────────────────────────────────────────────────────────
    if search_type in ("projects", "all"):
        proj_stmt = (
            select(Project)
            .where(
                or_(
                    Project.name.ilike(search_term),
                    Project.type.ilike(search_term),
                )
            )
            .limit(limit)
        )
        if scope.get("state"):
            proj_stmt = proj_stmt.where(Project.states.any(scope["state"]))
        if scope.get("district"):
            proj_stmt = proj_stmt.where(Project.districts.any(scope["district"]))

        proj_rows = db.execute(proj_stmt).scalars().all()
        projects = [
            {
                "project_id": str(p.project_id),
                "name": p.name,
                "type": p.type,
                "status": p.status,
                "states": p.states,
                "districts": p.districts,
                "land_required_ha": p.land_required_ha,
                "land_acquired_ha": p.land_acquired_ha,
                "_match_type": "project",
            }
            for p in proj_rows
        ]

    # ── Parcel search ─────────────────────────────────────────────────────────
    if search_type in ("parcels", "all"):
        parcel_stmt = (
            select(Parcel)
            .where(
                or_(
                    Parcel.survey_number.ilike(search_term),
                    Parcel.owner_name.ilike(search_term),
                    Parcel.village.ilike(search_term),
                    Parcel.district.ilike(search_term),
                )
            )
            .limit(limit)
        )
        if scope.get("state"):
            parcel_stmt = parcel_stmt.where(Parcel.state == scope["state"])
        if scope.get("district"):
            parcel_stmt = parcel_stmt.where(Parcel.district == scope["district"])

        parcel_rows = db.execute(parcel_stmt).scalars().all()
        parcels = [
            {
                "parcel_id": str(p.parcel_id),
                "project_id": str(p.project_id),
                "survey_number": p.survey_number,
                "owner_name": p.owner_name,
                "village": p.village,
                "district": p.district,
                "state": p.state,
                "current_stage": p.current_stage,
                "status": p.status,
                "risk_score": p.risk_score,
                "area_ha": p.area_ha,
                "_match_type": "parcel",
            }
            for p in parcel_rows
        ]

    total_count = len(projects) + len(parcels)

    return {
        "query": q,
        "total_count": total_count,
        "projects": projects,
        "parcels": parcels,
    }
