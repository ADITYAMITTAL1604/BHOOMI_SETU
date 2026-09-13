"""FastAPI router for /sla — SLA monitoring dashboard endpoints with strict RBAC."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_user_geographic_scope
from app.database import get_db
from app.models import AcquisitionStage, Parcel, Project, User
from app.models.enums import StageStatus
from app.services.sla_service import compute_stage_sla, STAGE_SLA_DAYS

router = APIRouter()


def _enforce_sla_scope(stmt, user: User, state_param: Optional[str] = None, district_param: Optional[str] = None):
    """Apply strict geographic scope enforcement for SLA queries.
    
    If a scoped officer attempts to query outside their state/district,
    raises HTTP 403. Otherwise binds Parcel filters to their jurisdiction.
    """
    scope = get_user_geographic_scope(user)
    
    # 1. State scope enforcement
    if scope.get("state"):
        if state_param and state_param.lower() != scope["state"].lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: state '{state_param}' is outside your assigned jurisdiction '{scope['state']}'",
            )
        stmt = stmt.where(func.lower(Parcel.state) == scope["state"].lower())
    elif state_param and state_param != "All States":
        stmt = stmt.where(Parcel.state == state_param)

    # 2. District scope enforcement
    if scope.get("district"):
        if district_param and district_param.lower() != scope["district"].lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: district '{district_param}' is outside your assigned jurisdiction '{scope['district']}'",
            )
        stmt = stmt.where(func.lower(Parcel.district) == scope["district"].lower())
    elif district_param:
        stmt = stmt.where(Parcel.district == district_param)

    return stmt


@router.get(
    "/dashboard",
    summary="SLA monitoring dashboard — aggregated breach/warning/ok counts",
    response_model=dict,
)
def sla_dashboard(
    project_id: Optional[UUID] = Query(None),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return SLA dashboard with green/yellow/red counts and stage breakdown. Scope-enforced."""
    stmt = (
        select(AcquisitionStage)
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(AcquisitionStage.status.in_([StageStatus.IN_PROGRESS.value, StageStatus.BLOCKED.value, "BLOCKED"]))
    )

    stmt = _enforce_sla_scope(stmt, current_user, state_param=state, district_param=district)

    if project_id:
        stmt = stmt.where(Parcel.project_id == project_id)

    stages = db.execute(stmt).scalars().all()

    ok_count = 0
    warning_count = 0
    critical_count = 0
    stage_breakdown = {}

    for stage in stages:
        sla = compute_stage_sla(stage)
        severity = sla["breach_severity"]

        if severity == "ok":
            ok_count += 1
        elif severity == "warning":
            warning_count += 1
        elif severity == "critical":
            critical_count += 1

        # Stage-level aggregation
        s_name = str(stage.stage_name)
        if s_name not in stage_breakdown:
            stage_breakdown[s_name] = {
                "stage_name": s_name,
                "total": 0,
                "ok": 0,
                "warning": 0,
                "critical": 0,
                "avg_days_pending": 0,
                "sla_days": STAGE_SLA_DAYS.get(s_name, 60),
            }

        stage_breakdown[s_name]["total"] += 1
        stage_breakdown[s_name][severity] += 1
        stage_breakdown[s_name]["avg_days_pending"] += sla["days_pending"]

    # Calculate averages
    for s_name, data in stage_breakdown.items():
        if data["total"] > 0:
            data["avg_days_pending"] = round(data["avg_days_pending"] / data["total"], 1)

    user_scope = get_user_geographic_scope(current_user)
    return {
        "summary": {
            "total_active_stages": len(stages),
            "ok": ok_count,
            "warning": warning_count,
            "critical": critical_count,
            "breach_rate": round(critical_count / max(1, len(stages)) * 100, 1),
        },
        "stage_breakdown": list(stage_breakdown.values()),
        "filters_applied": {
            "project_id": str(project_id) if project_id else None,
            "state": user_scope.get("state") or state,
            "district": user_scope.get("district") or district,
        },
        "user_jurisdiction": {
            "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            "state": user_scope.get("state"),
            "district": user_scope.get("district"),
        },
    }


@router.get(
    "/stage-delays",
    summary="Stage-wise delay analysis",
    response_model=dict,
)
def stage_delays(
    project_id: Optional[UUID] = Query(None),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return delay analysis broken down by acquisition stage. Scope-enforced."""
    stmt = (
        select(AcquisitionStage)
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(AcquisitionStage.status.in_([StageStatus.IN_PROGRESS.value, StageStatus.BLOCKED.value, "BLOCKED"]))
    )

    stmt = _enforce_sla_scope(stmt, current_user, state_param=state, district_param=district)

    if project_id:
        stmt = stmt.where(Parcel.project_id == project_id)

    stages = db.execute(stmt).scalars().all()

    delays = {}
    for stage in stages:
        sla = compute_stage_sla(stage)
        s_name = str(stage.stage_name)

        if s_name not in delays:
            delays[s_name] = {
                "stage_name": s_name,
                "sla_days": STAGE_SLA_DAYS.get(s_name, 60),
                "total_parcels": 0,
                "breached_parcels": 0,
                "avg_days_pending": 0,
                "max_days_pending": 0,
                "total_days_overdue": 0,
            }

        delays[s_name]["total_parcels"] += 1
        delays[s_name]["avg_days_pending"] += sla["days_pending"]
        delays[s_name]["max_days_pending"] = max(
            delays[s_name]["max_days_pending"], sla["days_pending"]
        )
        if sla["is_breached"]:
            delays[s_name]["breached_parcels"] += 1
            if sla["days_until_deadline"] is not None:
                delays[s_name]["total_days_overdue"] += abs(sla["days_until_deadline"])

    # Calculate averages
    for data in delays.values():
        if data["total_parcels"] > 0:
            data["avg_days_pending"] = round(
                data["avg_days_pending"] / data["total_parcels"], 1
            )
            data["avg_days_overdue"] = round(
                data["total_days_overdue"] / max(1, data["breached_parcels"]), 1
            )
            data["breach_rate"] = round(
                data["breached_parcels"] / data["total_parcels"] * 100, 1
            )
        else:
            data["avg_days_overdue"] = 0
            data["breach_rate"] = 0

    return {"delays": list(delays.values())}


@router.get(
    "/district-delays",
    summary="District-wise delay analysis",
    response_model=dict,
)
def district_delays(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    project_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return delay analysis broken down by district. Scope-enforced."""
    stmt = (
        select(AcquisitionStage, Parcel.district, Parcel.state)
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(AcquisitionStage.status.in_([StageStatus.IN_PROGRESS.value, StageStatus.BLOCKED.value, "BLOCKED"]))
    )

    stmt = _enforce_sla_scope(stmt, current_user, state_param=state, district_param=district)

    if project_id:
        stmt = stmt.where(Parcel.project_id == project_id)

    rows = db.execute(stmt).all()

    district_data = {}
    for stage, dist, st in rows:
        sla = compute_stage_sla(stage)
        key = f"{st}|{dist}"

        if key not in district_data:
            district_data[key] = {
                "state": st,
                "district": dist,
                "total_stages": 0,
                "breached": 0,
                "warning": 0,
                "ok": 0,
                "avg_days_pending": 0,
            }

        district_data[key]["total_stages"] += 1
        district_data[key]["avg_days_pending"] += sla["days_pending"]
        severity = sla["breach_severity"]
        if severity == "critical":
            district_data[key]["breached"] += 1
        elif severity == "warning":
            district_data[key]["warning"] += 1
        else:
            district_data[key]["ok"] += 1

    for data in district_data.values():
        if data["total_stages"] > 0:
            data["avg_days_pending"] = round(
                data["avg_days_pending"] / data["total_stages"], 1
            )
            data["breach_rate"] = round(
                data["breached"] / data["total_stages"] * 100, 1
            )
        else:
            data["breach_rate"] = 0

    return {"districts": list(district_data.values())}


@router.get(
    "/project-delays",
    summary="Project-wise delay analysis",
    response_model=dict,
)
def project_delays(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return delay analysis broken down by project. Scope-enforced."""
    stmt = (
        select(AcquisitionStage, Project.project_id, Project.name, Project.type)
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .join(Project, Project.project_id == Parcel.project_id)
        .where(AcquisitionStage.status.in_([StageStatus.IN_PROGRESS.value, StageStatus.BLOCKED.value, "BLOCKED"]))
    )

    stmt = _enforce_sla_scope(stmt, current_user, state_param=state, district_param=district)

    rows = db.execute(stmt).all()

    project_data = {}
    project_stage_breaches = {}

    for stage, pid, pname, ptype in rows:
        sla = compute_stage_sla(stage)
        key = str(pid)

        if key not in project_data:
            project_data[key] = {
                "project_id": key,
                "project_name": pname,
                "project_type": ptype,
                "total_stages": 0,
                "breached": 0,
                "warning": 0,
                "ok": 0,
                "avg_days_pending": 0,
                "total_days_overdue": 0,
                "worst_stage": None,
            }
            project_stage_breaches[key] = {}

        project_data[key]["total_stages"] += 1
        project_data[key]["avg_days_pending"] += sla["days_pending"]
        
        s_name = str(stage.stage_name)
        if s_name not in project_stage_breaches[key]:
            project_stage_breaches[key][s_name] = 0

        severity = sla["breach_severity"]
        if severity == "critical":
            project_data[key]["breached"] += 1
            project_stage_breaches[key][s_name] += 1
            if sla.get("days_until_deadline") is not None:
                project_data[key]["total_days_overdue"] += abs(sla["days_until_deadline"])
        elif severity == "warning":
            project_data[key]["warning"] += 1
        else:
            project_data[key]["ok"] += 1

    for key, data in project_data.items():
        if data["total_stages"] > 0:
            data["avg_days_pending"] = round(
                data["avg_days_pending"] / data["total_stages"], 1
            )
            data["breach_rate"] = round(
                data["breached"] / data["total_stages"] * 100, 1
            )
            data["avg_days_overdue"] = round(
                data["total_days_overdue"] / max(1, data["breached"]), 1
            )
        else:
            data["breach_rate"] = 0
            data["avg_days_overdue"] = 0

        # Compute worst stage (stage with most breaches)
        s_map = project_stage_breaches.get(key, {})
        if s_map:
            worst = max(s_map.items(), key=lambda x: x[1])[0]
            data["worst_stage"] = worst
        else:
            data["worst_stage"] = "COMPENSATION"

    result = sorted(
        project_data.values(),
        key=lambda x: x["breached"],
        reverse=True,
    )
    return {"projects": result}
