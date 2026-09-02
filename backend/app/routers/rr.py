"""FastAPI router for /rr — Rehabilitation & Resettlement records and summary."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Parcel, Project, RRRecord
from app.models.enums import AffectedType, RehabilitationStatus

router = APIRouter()


@router.get(
    "",
    summary="List R&R records with filters",
    response_model=dict,
)
def list_rr_records(
    project_id: Optional[UUID] = Query(None),
    parcel_id: Optional[UUID] = Query(None),
    rehabilitation_status: Optional[str] = Query(None),
    paf_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Paginated R&R records filtered by project, parcel, rehabilitation status, or PAF type."""
    stmt = select(RRRecord).join(Parcel, Parcel.parcel_id == RRRecord.parcel_id)

    if project_id:
        stmt = stmt.where(Parcel.project_id == project_id)
    if parcel_id:
        stmt = stmt.where(RRRecord.parcel_id == parcel_id)
    if rehabilitation_status:
        stmt = stmt.where(RRRecord.rehabilitation_status == rehabilitation_status)
    if paf_type:
        stmt = stmt.where(RRRecord.paf_type == paf_type)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    offset = (page - 1) * page_size
    records = db.execute(stmt.order_by(RRRecord.created_at.desc()).offset(offset).limit(page_size)).scalars().all()

    return {
        "items": [_serialize_rr(r) for r in records],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, -(-total // page_size)),
        },
    }


@router.get(
    "/summary",
    summary="Aggregate R&R summary by project",
    response_model=dict,
)
def get_rr_summary(
    project_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Return affected family counts, rehab status breakdown, and relocation metrics."""
    base = select(RRRecord).join(Parcel, Parcel.parcel_id == RRRecord.parcel_id)
    if project_id:
        base = base.where(Parcel.project_id == project_id)

    # Aggregates
    agg = db.execute(
        select(
            func.count(RRRecord.rr_id).label("total_families"),
            func.coalesce(func.sum(RRRecord.family_size), 0).label("total_persons"),
            func.coalesce(func.sum(RRRecord.affected_area_ha), 0.0).label("total_area"),
            func.coalesce(func.sum(RRRecord.compensation_paid), 0.0).label("total_comp_paid"),
        ).join(Parcel, Parcel.parcel_id == RRRecord.parcel_id)
        .where(*([] if not project_id else [Parcel.project_id == project_id]))
    ).one()

    # Status breakdown
    status_counts = dict(
        db.execute(
            select(RRRecord.rehabilitation_status, func.count(RRRecord.rr_id))
            .join(Parcel, Parcel.parcel_id == RRRecord.parcel_id)
            .where(*([] if not project_id else [Parcel.project_id == project_id]))
            .group_by(RRRecord.rehabilitation_status)
        ).all()
    )

    # PAF type breakdown
    paf_counts = dict(
        db.execute(
            select(RRRecord.paf_type, func.count(RRRecord.rr_id))
            .join(Parcel, Parcel.parcel_id == RRRecord.parcel_id)
            .where(*([] if not project_id else [Parcel.project_id == project_id]))
            .group_by(RRRecord.paf_type)
        ).all()
    )

    # Relocation metrics
    families_with_plots = db.execute(
        select(func.count(RRRecord.rr_id))
        .join(Parcel, Parcel.parcel_id == RRRecord.parcel_id)
        .where(
            *([] if not project_id else [Parcel.project_id == project_id]),
            RRRecord.plot_allotted.isnot(None),
        )
    ).scalar() or 0

    families_with_relocation = db.execute(
        select(func.count(RRRecord.rr_id))
        .join(Parcel, Parcel.parcel_id == RRRecord.parcel_id)
        .where(
            *([] if not project_id else [Parcel.project_id == project_id]),
            RRRecord.relocation_site.isnot(None),
        )
    ).scalar() or 0

    total_families = int(agg.total_families)
    families_completed = status_counts.get(RehabilitationStatus.COMPLETED.value, 0)

    return {
        "project_id": str(project_id) if project_id else "all",
        "summary": {
            "total_affected_families": total_families,
            "total_affected_persons": int(agg.total_persons),
            "total_affected_area_ha": round(float(agg.total_area), 2),
            "total_compensation_paid": round(float(agg.total_comp_paid), 2),
            "families_rehabilitated": families_completed,
            "families_pending": total_families - families_completed,
            "plots_allotted": families_with_plots,
            "relocation_sites_assigned": families_with_relocation,
        },
        "rehabilitation_status_breakdown": status_counts,
        "paf_type_breakdown": paf_counts,
    }


def _serialize_rr(r: RRRecord) -> dict:
    return {
        "rr_id": str(r.rr_id),
        "parcel_id": str(r.parcel_id),
        "paf_name": r.paf_name,
        "paf_type": r.paf_type,
        "family_size": r.family_size,
        "affected_area_ha": float(r.affected_area_ha or 0),
        "rehabilitation_status": r.rehabilitation_status,
        "compensation_paid": float(r.compensation_paid or 0),
        "relocation_site": r.relocation_site,
        "plot_allotted": r.plot_allotted,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
