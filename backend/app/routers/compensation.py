"""FastAPI router for /compensation — compensation records and summary aggregations."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_district_or_above
from app.database import get_db
from app.models import Compensation, Parcel, Project
from app.models.enums import CompensationPaymentStatus

router = APIRouter()


class CompensationUpdateRequest(BaseModel):
    payment_status: Optional[str] = None
    paid_amount: Optional[float] = None
    remarks: Optional[str] = None


# ── List ──────────────────────────────────────────────────────────────────────

@router.get(
    "",
    summary="List compensation records with aggregates",
    response_model=dict,
)
def list_compensation(
    project_id: Optional[UUID] = Query(None),
    parcel_id: Optional[UUID] = Query(None),
    payment_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Paginated compensation records with total_assessed, total_approved, total_paid, total_pending."""
    stmt = select(Compensation).join(Parcel, Parcel.parcel_id == Compensation.parcel_id)

    if project_id:
        stmt = stmt.where(Parcel.project_id == project_id)
    if parcel_id:
        stmt = stmt.where(Compensation.parcel_id == parcel_id)
    if payment_status:
        stmt = stmt.where(Compensation.payment_status == payment_status)

    # Aggregates
    agg_stmt = select(
        func.coalesce(func.sum(Compensation.assessed_amount), 0.0).label("total_assessed"),
        func.coalesce(func.sum(Compensation.approved_amount), 0.0).label("total_approved"),
        func.coalesce(func.sum(Compensation.paid_amount), 0.0).label("total_paid"),
    ).join(Parcel, Parcel.parcel_id == Compensation.parcel_id)
    if project_id:
        agg_stmt = agg_stmt.where(Parcel.project_id == project_id)
    if parcel_id:
        agg_stmt = agg_stmt.where(Compensation.parcel_id == parcel_id)
    if payment_status:
        agg_stmt = agg_stmt.where(Compensation.payment_status == payment_status)

    agg = db.execute(agg_stmt).one()
    total_approved = float(agg.total_approved)
    total_paid = float(agg.total_paid)

    total_count = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    offset = (page - 1) * page_size
    records = db.execute(stmt.order_by(Compensation.created_at.desc()).offset(offset).limit(page_size)).scalars().all()

    return {
        "items": [_serialize_comp(c) for c in records],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": max(1, -(-total_count // page_size)),
        },
        "aggregates": {
            "total_assessed": round(float(agg.total_assessed), 2),
            "total_approved": round(total_approved, 2),
            "total_paid": round(total_paid, 2),
            "total_pending": round(max(0.0, total_approved - total_paid), 2),
            "disbursement_pct": round(total_paid / max(1.0, total_approved) * 100, 1),
        },
    }


# ── Summary (per-project breakdown) ──────────────────────────────────────────

@router.get(
    "/summary",
    summary="Project-level compensation breakdown",
    response_model=dict,
)
def get_compensation_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Return compensation aggregates per project."""
    rows = db.execute(
        select(
            Parcel.project_id,
            func.count(Compensation.compensation_id).label("parcel_count"),
            func.coalesce(func.sum(Compensation.assessed_amount), 0.0).label("assessed"),
            func.coalesce(func.sum(Compensation.approved_amount), 0.0).label("approved"),
            func.coalesce(func.sum(Compensation.paid_amount), 0.0).label("paid"),
        )
        .join(Parcel, Parcel.parcel_id == Compensation.parcel_id)
        .group_by(Parcel.project_id)
    ).all()

    project_ids = [row[0] for row in rows]
    proj_names = {}
    if project_ids:
        projs = db.execute(
            select(Project.project_id, Project.name).where(Project.project_id.in_(project_ids))
        ).all()
        proj_names = {
            str(p[0] if isinstance(p, (list, tuple)) else getattr(p, "project_id", p)): (
                p[1] if isinstance(p, (list, tuple)) else getattr(p, "name", "")
            )
            for p in projs
        }

    return {
        "projects": [
            {
                "project_id": str(row[0]),
                "project_name": proj_names.get(str(row[0]), "Unknown"),
                "parcel_count": row[1],
                "total_assessed": round(float(row[2]), 2),
                "total_approved": round(float(row[3]), 2),
                "total_paid": round(float(row[4]), 2),
                "total_pending": round(max(0.0, float(row[3]) - float(row[4])), 2),
                "disbursement_pct": round(float(row[4]) / max(1.0, float(row[3])) * 100, 1),
            }
            for row in rows
        ]
    }


# ── Update ────────────────────────────────────────────────────────────────────

@router.put(
    "/{compensation_id}",
    summary="Update compensation payment status and amount",
    response_model=dict,
)
def update_compensation(
    compensation_id: UUID,
    body: CompensationUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_district_or_above),
) -> dict:
    """Update payment_status, paid_amount, or remarks for a compensation record."""
    comp = db.execute(
        select(Compensation).where(Compensation.compensation_id == compensation_id)
    ).scalar_one_or_none()

    if not comp:
        raise HTTPException(status_code=404, detail="Compensation record not found.")

    if body.payment_status is not None:
        comp.payment_status = body.payment_status
    if body.paid_amount is not None:
        comp.paid_amount = body.paid_amount
    if body.remarks is not None:
        comp.remarks = body.remarks

    db.commit()
    db.refresh(comp)
    return _serialize_comp(comp)


# ── Serializer ────────────────────────────────────────────────────────────────

def _serialize_comp(c: Compensation) -> dict:
    return {
        "compensation_id": str(c.compensation_id),
        "parcel_id": str(c.parcel_id),
        "assessed_amount": float(c.assessed_amount or 0),
        "approved_amount": float(c.approved_amount or 0),
        "paid_amount": float(c.paid_amount or 0),
        "pending_amount": max(0.0, float(c.approved_amount or 0) - float(c.paid_amount or 0)),
        "payment_status": c.payment_status,
        "payment_date": c.payment_date.isoformat() if c.payment_date else None,
        "remarks": c.remarks,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
