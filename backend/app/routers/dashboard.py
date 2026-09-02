"""FastAPI router for /dashboard summary and analytics endpoints."""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin, require_state_or_above
from app.database import get_db
from app.models import Project, Parcel, AcquisitionStage, AuditLog, User, Compensation, RRRecord
from app.models.enums import ParcelStatus, ProjectStatus, StageStatus, StageName, RehabilitationStatus

router = APIRouter()


# ── National Dashboard ────────────────────────────────────────────────────────

@router.get(
    "/national",
    summary="Get national aggregate land acquisition dashboard metrics",
    response_model=dict,
)
def get_national_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Return high-level national dashboard aggregate metrics."""
    from app.core.deps import get_user_geographic_scope
    scope = get_user_geographic_scope(current_user)

    proj_stmt = select(
        func.count(Project.project_id).label("total_projects"),
        func.coalesce(func.sum(Project.land_required_ha), 0.0).label("total_land_required_ha"),
        func.coalesce(func.sum(Project.land_acquired_ha), 0.0).label("total_land_acquired_ha"),
    )
    if scope.get("state"):
        proj_stmt = proj_stmt.where(Project.states.any(scope["state"]))
    if scope.get("district"):
        proj_stmt = proj_stmt.where(Project.districts.any(scope["district"]))
    proj_totals = db.execute(proj_stmt).one()

    proj_status_stmt = select(Project.status, func.count(Project.project_id))
    if scope.get("state"):
        proj_status_stmt = proj_status_stmt.where(Project.states.any(scope["state"]))
    if scope.get("district"):
        proj_status_stmt = proj_status_stmt.where(Project.districts.any(scope["district"]))
    proj_status_counts = dict(db.execute(proj_status_stmt.group_by(Project.status)).all())

    proj_type_stmt = select(Project.type, func.count(Project.project_id))
    if scope.get("state"):
        proj_type_stmt = proj_type_stmt.where(Project.states.any(scope["state"]))
    if scope.get("district"):
        proj_type_stmt = proj_type_stmt.where(Project.districts.any(scope["district"]))
    proj_type_counts = dict(db.execute(proj_type_stmt.group_by(Project.type)).all())

    parcel_stmt = select(
        func.count(Parcel.parcel_id).label("total_parcels"),
        func.coalesce(func.sum(Parcel.area_ha), 0.0).label("total_parcel_area_ha"),
        func.coalesce(func.avg(Parcel.risk_score), 0.0).label("avg_risk_score"),
    )
    if scope.get("state"):
        parcel_stmt = parcel_stmt.where(Parcel.state == scope["state"])
    if scope.get("district"):
        parcel_stmt = parcel_stmt.where(Parcel.district == scope["district"])
    parcel_totals = db.execute(parcel_stmt).one()

    parcel_status_stmt = select(Parcel.status, func.count(Parcel.parcel_id))
    if scope.get("state"):
        parcel_status_stmt = parcel_status_stmt.where(Parcel.state == scope["state"])
    if scope.get("district"):
        parcel_status_stmt = parcel_status_stmt.where(Parcel.district == scope["district"])
    parcel_status_counts = dict(db.execute(parcel_status_stmt.group_by(Parcel.status)).all())

    parcel_stage_stmt = select(Parcel.current_stage, func.count(Parcel.parcel_id))
    if scope.get("state"):
        parcel_stage_stmt = parcel_stage_stmt.where(Parcel.state == scope["state"])
    if scope.get("district"):
        parcel_stage_stmt = parcel_stage_stmt.where(Parcel.district == scope["district"])
    parcel_stage_counts = dict(db.execute(parcel_stage_stmt.group_by(Parcel.current_stage)).all())

    high_risk_stmt = select(func.count(Parcel.parcel_id)).where(Parcel.risk_score >= 70.0)
    if scope.get("state"):
        high_risk_stmt = high_risk_stmt.where(Parcel.state == scope["state"])
    if scope.get("district"):
        high_risk_stmt = high_risk_stmt.where(Parcel.district == scope["district"])
    high_risk_count = db.execute(high_risk_stmt).scalar() or 0

    today = datetime.now(timezone.utc).date()
    sla_breach_stmt = (
        select(func.count(AcquisitionStage.stage_id))
        .where(
            AcquisitionStage.status == StageStatus.IN_PROGRESS.value,
            AcquisitionStage.target_date.isnot(None),
            AcquisitionStage.target_date < today,
        )
    )
    sla_breaches_count = db.execute(sla_breach_stmt).scalar() or 0

    districts_stmt = (
        select(Parcel.district, Parcel.state, func.count(Parcel.parcel_id).label("parcels_count"))
        .where(Parcel.district != "")
        .group_by(Parcel.district, Parcel.state)
        .order_by(desc("parcels_count"))
        .limit(6)
    )
    if scope.get("state"):
        districts_stmt = districts_stmt.where(Parcel.state == scope["state"])
    top_districts = [
        {"district": row[0], "state": row[1], "parcel_count": row[2]}
        for row in db.execute(districts_stmt).all()
    ]

    audit_stmt = (
        select(AuditLog.action, AuditLog.entity_type, AuditLog.entity_id, AuditLog.created_at, AuditLog.new_values)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    recent_activity = [
        {
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": str(row.entity_id),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "details": row.new_values,
        }
        for row in db.execute(audit_stmt).all()
    ]

    land_req = float(proj_totals.total_land_required_ha)
    land_acq = float(proj_totals.total_land_acquired_ha)
    progress_pct = round((land_acq / land_req * 100), 2) if land_req > 0 else 0.0

    return {
        "summary": {
            "total_projects": proj_totals.total_projects,
            "total_parcels": parcel_totals.total_parcels,
            "total_land_required_ha": round(land_req, 2),
            "total_land_acquired_ha": round(land_acq, 2),
            "overall_acquisition_progress_pct": progress_pct,
            "total_parcel_area_ha": round(float(parcel_totals.total_parcel_area_ha), 2),
            "avg_risk_score": round(float(parcel_totals.avg_risk_score), 2),
            "high_risk_parcels_count": high_risk_count,
            "active_sla_breaches": sla_breaches_count,
        },
        "projects_by_status": proj_status_counts,
        "projects_by_type": proj_type_counts,
        "parcels_by_status": parcel_status_counts,
        "parcels_by_stage": parcel_stage_counts,
        "top_districts": top_districts,
        "recent_activity": recent_activity,
    }


# ── State Dashboard ───────────────────────────────────────────────────────────

def _to_dict_safe(rows) -> dict:
    res = {}
    for r in rows:
        if isinstance(r, (list, tuple)) and len(r) >= 2:
            res[r[0]] = r[1]
        elif hasattr(r, "__getitem__"):
            try:
                res[r[0]] = r[1]
            except Exception:
                pass
    return res


def _extract_comp(comp):
    if isinstance(comp, (list, tuple)):
        assessed = float(comp[0] or 0) if len(comp) > 0 else 0.0
        approved = float(comp[1] or 0) if len(comp) > 1 else 0.0
        paid = float(comp[2] or 0) if len(comp) > 2 else 0.0
    else:
        def _to_float(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        assessed = _to_float(getattr(comp, "total_assessed", None)) or _to_float(getattr(comp, "assessed", None))
        approved = _to_float(getattr(comp, "total_approved", None)) or _to_float(getattr(comp, "approved", None))
        paid = _to_float(getattr(comp, "total_paid", None)) or _to_float(getattr(comp, "paid", None))
    return assessed, approved, paid


@router.get(
    "/state/{state_name}",
    summary="State-scoped land acquisition dashboard",
    response_model=dict,
)
def get_state_dashboard(
    state_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Aggregate dashboard scoped to a specific state."""
    today = datetime.now(timezone.utc).date()

    # Projects in this state
    proj_totals = db.execute(
        select(
            func.count(Project.project_id).label("total"),
            func.coalesce(func.sum(Project.land_required_ha), 0.0).label("required"),
            func.coalesce(func.sum(Project.land_acquired_ha), 0.0).label("acquired"),
        ).where(Project.states.any(state_name))
    ).one()

    proj_by_status = _to_dict_safe(
        db.execute(
            select(Project.status, func.count(Project.project_id))
            .where(Project.states.any(state_name))
            .group_by(Project.status)
        ).all()
    )

    # Parcels in this state
    parcel_totals = db.execute(
        select(
            func.count(Parcel.parcel_id).label("total"),
            func.coalesce(func.sum(Parcel.area_ha), 0.0).label("area"),
            func.coalesce(func.avg(Parcel.risk_score), 0.0).label("avg_risk"),
        ).where(Parcel.state == state_name)
    ).one()

    parcel_by_status = _to_dict_safe(
        db.execute(
            select(Parcel.status, func.count(Parcel.parcel_id))
            .where(Parcel.state == state_name)
            .group_by(Parcel.status)
        ).all()
    )

    parcel_by_stage = _to_dict_safe(
        db.execute(
            select(Parcel.current_stage, func.count(Parcel.parcel_id))
            .where(Parcel.state == state_name)
            .group_by(Parcel.current_stage)
        ).all()
    )

    # SLA breaches within state
    sla_breach_count = db.execute(
        select(func.count(AcquisitionStage.stage_id))
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(
            Parcel.state == state_name,
            AcquisitionStage.status == StageStatus.IN_PROGRESS.value,
            AcquisitionStage.target_date.isnot(None),
            AcquisitionStage.target_date < today,
        )
    ).scalar() or 0

    # Top districts by parcel count
    top_districts = [
        {"district": row[0], "parcel_count": row[1], "avg_risk": round(float(row[2] or 0), 2)}
        for row in db.execute(
            select(
                Parcel.district,
                func.count(Parcel.parcel_id),
                func.avg(Parcel.risk_score),
            )
            .where(Parcel.state == state_name, Parcel.district != "")
            .group_by(Parcel.district)
            .order_by(desc(func.count(Parcel.parcel_id)))
            .limit(8)
        ).all()
    ]

    # Compensation summary for this state
    comp = db.execute(
        select(
            func.coalesce(func.sum(Compensation.assessed_amount), 0.0),
            func.coalesce(func.sum(Compensation.approved_amount), 0.0),
            func.coalesce(func.sum(Compensation.paid_amount), 0.0),
        ).join(Parcel, Parcel.parcel_id == Compensation.parcel_id)
        .where(Parcel.state == state_name)
    ).one()

    comp_assessed, comp_approved, comp_paid = _extract_comp(comp)

    land_req = float(proj_totals.required)
    land_acq = float(proj_totals.acquired)
    progress_pct = round(land_acq / land_req * 100, 2) if land_req > 0 else 0.0

    return {
        "state": state_name,
        "summary": {
            "total_projects": proj_totals.total,
            "total_parcels": parcel_totals.total,
            "total_parcel_area_ha": round(float(parcel_totals.area), 2),
            "land_required_ha": round(land_req, 2),
            "land_acquired_ha": round(land_acq, 2),
            "acquisition_progress_pct": progress_pct,
            "avg_risk_score": round(float(parcel_totals.avg_risk), 2),
            "sla_breaches": sla_breach_count,
        },
        "projects_by_status": proj_by_status,
        "parcels_by_status": parcel_by_status,
        "parcels_by_stage": parcel_by_stage,
        "top_districts": top_districts,
        "compensation": {
            "total_assessed": round(comp_assessed, 2),
            "total_approved": round(comp_approved, 2),
            "total_paid": round(comp_paid, 2),
            "total_pending": round(max(0.0, comp_approved - comp_paid), 2),
        },
    }


# ── District Dashboard ────────────────────────────────────────────────────────

@router.get(
    "/district/{district_name}",
    summary="District-scoped land acquisition dashboard",
    response_model=dict,
)
def get_district_dashboard(
    district_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Aggregate dashboard scoped to a specific district."""
    today = datetime.now(timezone.utc).date()

    parcel_totals = db.execute(
        select(
            func.count(Parcel.parcel_id).label("total"),
            func.coalesce(func.sum(Parcel.area_ha), 0.0).label("area"),
            func.coalesce(func.avg(Parcel.risk_score), 0.0).label("avg_risk"),
        ).where(Parcel.district == district_name)
    ).one()

    parcel_by_status = _to_dict_safe(
        db.execute(
            select(Parcel.status, func.count(Parcel.parcel_id))
            .where(Parcel.district == district_name)
            .group_by(Parcel.status)
        ).all()
    )

    parcel_by_stage = _to_dict_safe(
        db.execute(
            select(Parcel.current_stage, func.count(Parcel.parcel_id))
            .where(Parcel.district == district_name)
            .group_by(Parcel.current_stage)
        ).all()
    )

    high_risk_count = db.execute(
        select(func.count(Parcel.parcel_id))
        .where(Parcel.district == district_name, Parcel.risk_score >= 70.0)
    ).scalar() or 0

    # SLA breaches in district
    sla_breach_count = db.execute(
        select(func.count(AcquisitionStage.stage_id))
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(
            Parcel.district == district_name,
            AcquisitionStage.status == StageStatus.IN_PROGRESS.value,
            AcquisitionStage.target_date.isnot(None),
            AcquisitionStage.target_date < today,
        )
    ).scalar() or 0

    # Per-stage SLA timer: days_pending, breach count
    stage_sla_rows = db.execute(
        select(
            AcquisitionStage.stage_name,
            func.count(AcquisitionStage.stage_id).label("total"),
            func.count(AcquisitionStage.stage_id).filter(
                AcquisitionStage.target_date < today
            ).label("breached"),
        )
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(
            Parcel.district == district_name,
            AcquisitionStage.status == StageStatus.IN_PROGRESS.value,
        )
        .group_by(AcquisitionStage.stage_name)
    ).all()

    stage_sla_summary = []
    for row in stage_sla_rows:
        sn = row[0] if isinstance(row, (list, tuple)) else getattr(row, "stage_name", "UNKNOWN")
        tot = row[1] if isinstance(row, (list, tuple)) and len(row) > 1 else getattr(row, "total", 0)
        br = row[2] if isinstance(row, (list, tuple)) and len(row) > 2 else getattr(row, "breached", 0)
        rate = round(float(br) / max(1, int(tot)) * 100, 1)
        stage_sla_summary.append({
            "stage": str(sn),
            "active_count": int(tot),
            "breached_count": int(br),
            "breach_rate_pct": rate,
        })

    # Officer workload (count active parcels per officer)
    officer_rows = db.execute(
        select(Parcel.assigned_officer, func.count(Parcel.parcel_id).label("active_parcels"))
        .where(
            Parcel.district == district_name,
            Parcel.status.in_([ParcelStatus.IN_PROGRESS.value, ParcelStatus.BLOCKED.value]),
            Parcel.assigned_officer.isnot(None),
        )
        .group_by(Parcel.assigned_officer)
        .order_by(desc("active_parcels"))
        .limit(10)
    ).all()

    officer_workload = [
        {"officer_id": str(row[0]), "active_parcels": row[1]}
        for row in officer_rows
    ]

    # Compensation for district
    comp = db.execute(
        select(
            func.coalesce(func.sum(Compensation.assessed_amount), 0.0),
            func.coalesce(func.sum(Compensation.approved_amount), 0.0),
            func.coalesce(func.sum(Compensation.paid_amount), 0.0),
        ).join(Parcel, Parcel.parcel_id == Compensation.parcel_id)
        .where(Parcel.district == district_name)
    ).one()

    # R&R summary for district
    rr_total = db.execute(
        select(func.count(RRRecord.rr_id))
        .join(Parcel, Parcel.parcel_id == RRRecord.parcel_id)
        .where(Parcel.district == district_name)
    ).scalar() or 0

    rr_completed = db.execute(
        select(func.count(RRRecord.rr_id))
        .join(Parcel, Parcel.parcel_id == RRRecord.parcel_id)
        .where(
            Parcel.district == district_name,
            RRRecord.rehabilitation_status == RehabilitationStatus.COMPLETED.value,
        )
    ).scalar() or 0

    comp_assessed, comp_approved, comp_paid = _extract_comp(comp)

    return {
        "district": district_name,
        "summary": {
            "total_parcels": parcel_totals.total,
            "total_parcel_area_ha": round(float(parcel_totals.area), 2),
            "avg_risk_score": round(float(parcel_totals.avg_risk), 2),
            "high_risk_parcels": high_risk_count,
            "sla_breaches": sla_breach_count,
        },
        "parcels_by_status": parcel_by_status,
        "parcels_by_stage": parcel_by_stage,
        "stage_sla_summary": stage_sla_summary,
        "officer_workload": officer_workload,
        "compensation": {
            "total_assessed": round(comp_assessed, 2),
            "total_approved": round(comp_approved, 2),
            "total_paid": round(comp_paid, 2),
            "total_pending": round(max(0.0, comp_approved - comp_paid), 2),
            "disbursement_pct": round(
                comp_paid / max(1.0, comp_approved) * 100, 1
            ),
        },
        "rr": {
            "total_affected_families": rr_total,
            "families_rehabilitated": rr_completed,
            "pending_rehabilitation": rr_total - rr_completed,
        },
    }


# ── SLA Status Report ─────────────────────────────────────────────────────────

@router.get(
    "/sla-status",
    summary="Cross-project SLA timer status and breach report",
    response_model=dict,
)
def get_sla_status(
    project_id: Optional[UUID] = Query(None),
    run_sweep: bool = Query(False, description="If true, auto-update breached parcel statuses to BLOCKED"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Return per-stage SLA timer information (days_pending, is_breached, days_until_deadline).

    Optionally trigger an SLA sweep to auto-update parcel statuses.
    """
    from app.services.sla_service import compute_stage_sla, run_sla_sweep, STAGE_SLA_DAYS

    sweep_result = None
    if run_sweep:
        sweep_result = run_sla_sweep(db, project_id=project_id, create_alerts=True)

    today = datetime.now(timezone.utc).date()

    stmt = (
        select(AcquisitionStage, Parcel.survey_number, Parcel.district, Parcel.state, Parcel.project_id)
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(AcquisitionStage.status == StageStatus.IN_PROGRESS.value)
        .order_by(AcquisitionStage.target_date.asc().nulls_last())
        .limit(200)
    )
    if project_id:
        stmt = stmt.where(Parcel.project_id == project_id)

    rows = db.execute(stmt).all()

    stages_report = []
    breached_count = 0
    warning_count = 0

    for stage, survey_number, district, state, proj_id in rows:
        sla = compute_stage_sla(stage)
        sla["survey_number"] = survey_number
        sla["district"] = district
        sla["state"] = state
        sla["project_id"] = str(proj_id)
        sla["parcel_id"] = str(stage.parcel_id)
        stages_report.append(sla)
        if sla["is_breached"]:
            breached_count += 1
        elif sla["breach_severity"] == "warning":
            warning_count += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_active_stages": len(stages_report),
        "breached_count": breached_count,
        "warning_count": warning_count,
        "on_track_count": len(stages_report) - breached_count - warning_count,
        "sweep_result": sweep_result,
        "stages": stages_report,
    }
