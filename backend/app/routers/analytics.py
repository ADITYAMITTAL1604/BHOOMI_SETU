"""FastAPI router for /analytics — ML predictions, bottleneck, priority, and why-delayed endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, and_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.ml.delay_risk_service import get_delay_risk_service
from app.ml.features import build_features, STAGE_COMPLEXITY_WEIGHTS
from app.models import AcquisitionStage, Compensation, Parcel, Project, ProjectHistory
from app.models.enums import ParcelStatus, StageName, StageStatus

router = APIRouter()


# ── Shared helper: synthesize live snapshot ───────────────────────────────────

def _synthesize_live_snapshot(db: Session, project: Project) -> Dict[str, Any]:
    """Construct a current snapshot from live parcel, stage, and compensation tables."""
    parcels = db.execute(
        select(Parcel).where(Parcel.project_id == project.project_id)
    ).scalars().all()

    total_parcels = len(parcels)
    completed = sum(1 for p in parcels if p.status == ParcelStatus.COMPLETED.value)
    in_progress = sum(1 for p in parcels if p.status == ParcelStatus.IN_PROGRESS.value)
    blocked = sum(1 for p in parcels if p.status == ParcelStatus.BLOCKED.value)

    stage_counts: Dict[str, int] = {}
    for p in parcels:
        stage_counts[p.current_stage] = stage_counts.get(p.current_stage, 0) + 1

    comp_totals = db.execute(
        select(
            func.coalesce(func.sum(Compensation.paid_amount), 0.0).label("paid"),
            func.coalesce(func.sum(Compensation.approved_amount - Compensation.paid_amount), 0.0).label("pending"),
        )
        .join(Parcel, Parcel.parcel_id == Compensation.parcel_id)
        .where(Parcel.project_id == project.project_id)
    ).one()

    sla_breaches = db.execute(
        select(func.count(AcquisitionStage.stage_id))
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(
            Parcel.project_id == project.project_id,
            AcquisitionStage.status == StageStatus.IN_PROGRESS.value,
            AcquisitionStage.target_date.isnot(None),
            AcquisitionStage.target_date < func.current_date(),
        )
    ).scalar() or 0

    disputes = sum(1 for p in parcels if p.status in (ParcelStatus.DISPUTED.value, ParcelStatus.BLOCKED.value))

    return {
        "snapshot_date": project.updated_at or project.created_at,
        "land_required_ha": project.land_required_ha,
        "land_acquired_ha": project.land_acquired_ha,
        "parcels_total": total_parcels,
        "parcels_completed": completed,
        "parcels_in_progress": in_progress,
        "parcels_blocked": blocked,
        "compensation_paid_total": float(comp_totals.paid),
        "compensation_pending_total": max(0.0, float(comp_totals.pending)),
        "stages_snapshot": stage_counts,
        "metadata_json": {
            "sla_breaches": sla_breaches,
            "disputes_count": disputes,
            "officers_count": 4,
        },
    }


def _resolve_analytics_project(db: Session, project_id: str) -> Project:
    """Resolve project ID, supporting 'default' alias to return the first available project."""
    if not project_id or str(project_id).strip().lower() in ("default", "none", "null"):
        project = db.execute(select(Project).order_by(Project.created_at.desc())).scalars().first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No projects found in system",
            )
        return project

    try:
        pid_uuid = UUID(str(project_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid project ID: {project_id}",
        )

    project = db.execute(select(Project).where(Project.project_id == pid_uuid)).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


# ── Delay Risk Prediction ─────────────────────────────────────────────────────

@router.get(
    "/projects/{project_id}/delay-risk",
    summary="ML-driven delay risk prediction and SHAP explainability",
    response_model=dict,
)
def get_project_delay_risk(
    project_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Predict project delay probability with explainability factors (cached 60s)."""
    project = _resolve_analytics_project(db, project_id)
    resolved_id = project.project_id

    stmt = (
        select(ProjectHistory)
        .where(ProjectHistory.project_id == resolved_id)
        .order_by(ProjectHistory.snapshot_date.asc())
    )
    db_snapshots = db.execute(stmt).scalars().all()

    snapshot_dicts: List[Dict[str, Any]] = []
    for s in db_snapshots:
        snapshot_dicts.append({
            "snapshot_date": s.snapshot_date,
            "land_required_ha": float(s.land_required_ha),
            "land_acquired_ha": float(s.land_acquired_ha),
            "parcels_total": s.parcels_total,
            "parcels_completed": s.parcels_completed,
            "parcels_in_progress": s.parcels_in_progress,
            "parcels_blocked": s.parcels_blocked,
            "compensation_paid_total": float(s.compensation_paid_total),
            "compensation_pending_total": float(s.compensation_pending_total),
            "stages_snapshot": s.stages_snapshot or {},
            "metadata_json": s.metadata_json or {},
        })

    if len(snapshot_dicts) == 0:
        live_snap = _synthesize_live_snapshot(db, project)
        if live_snap.get("parcels_total", 0) > 0:
            snapshot_dicts.append(live_snap)

    project_meta = {
        "project_id": str(project.project_id),
        "name": project.name,
        "type": project.type,
        "states": project.states,
        "districts": project.districts,
        "land_required_ha": project.land_required_ha,
    }
    feature_row = build_features(snapshot_dicts, project_meta=project_meta)

    service = get_delay_risk_service()
    prediction_result = service.predict_delay_risk(
        feature_row,
        project_id=str(resolved_id),
        allow_demo_fallback=True,
    )

    # Ensure frontend compatibility keys are present
    feature_importance = prediction_result.get("feature_importance") or [
        {
            "feature": f.get("feature", ""),
            "label": f.get("title", f.get("feature", "").replace("_", " ").title()),
            "importance": f.get("shap_value", 0.0),
            "direction": "positive" if f.get("shap_value", 0.0) > 0 else "negative",
        }
        for f in prediction_result.get("top_factors", [])
    ]

    res_data = {
        "project_id": str(project.project_id),
        "project_name": project.name,
        "project_status": project.status,
        "snapshots_used": prediction_result.get("snapshots_used", len(snapshot_dicts) or 1),
        "insufficient_data": prediction_result.get("status") == "insufficient_data",
        "feature_importance": feature_importance,
        **prediction_result,
    }
    if res_data.get("risk_score") is None:
        res_data["risk_score"] = 0.25
    return res_data


# ── Bottleneck Analysis ───────────────────────────────────────────────────────

@router.get(
    "/bottleneck/{project_id}",
    summary="Per-stage bottleneck score and primary bottleneck identification",
    response_model=dict,
)
@router.get(
    "/projects/{project_id}/bottlenecks",
    summary="Per-stage bottleneck score and primary bottleneck identification",
    response_model=dict,
)
def get_project_bottleneck(
    project_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Compute bottleneck_score per stage and identify the primary bottleneck stage.

    bottleneck_score = avg_days_pending × sla_breach_rate × (blocked_count / max(1, total_in_stage))
    Normalized to [0, 1] across all 11 stages.
    """
    project = _resolve_analytics_project(db, project_id)
    resolved_id = project.project_id

    today = datetime.now(timezone.utc).date()

    # Fetch all acquisition stages for this project's parcels
    rows = db.execute(
        select(
            AcquisitionStage.stage_name,
            AcquisitionStage.status,
            AcquisitionStage.start_date,
            AcquisitionStage.target_date,
            Parcel.status.label("parcel_status"),
        )
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(Parcel.project_id == resolved_id)
    ).all()

    stage_data: Dict[str, Dict[str, Any]] = {
        name.value: {
            "total": 0,
            "in_progress": 0,
            "breached": 0,
            "blocked": 0,
            "days_list": [],
        }
        for name in StageName
    }

    for row in rows:
        sn = str(row.stage_name)
        if sn not in stage_data:
            stage_data[sn] = {
                "total": 0,
                "in_progress": 0,
                "breached": 0,
                "blocked": 0,
                "days_list": [],
            }
        d = stage_data[sn]
        d["total"] += 1
        if row.status == StageStatus.IN_PROGRESS.value:
            d["in_progress"] += 1
            if row.start_date:
                start = row.start_date if hasattr(row.start_date, "toordinal") else (row.start_date.date() if hasattr(row.start_date, "date") else None)
                if start:
                    d["days_list"].append((today - start).days)
            if row.target_date:
                target = row.target_date if hasattr(row.target_date, "toordinal") else (row.target_date.date() if hasattr(row.target_date, "date") else None)
                if target and target < today:
                    d["breached"] += 1
        if row.parcel_status in (ParcelStatus.BLOCKED.value, ParcelStatus.DISPUTED.value):
            d["blocked"] += 1

    # Compute raw bottleneck scores
    scores: Dict[str, float] = {}
    for stage_name, d in stage_data.items():
        in_progress = d["in_progress"]
        if in_progress == 0:
            scores[stage_name] = 0.0
            continue

        avg_days = sum(d["days_list"]) / len(d["days_list"]) if d["days_list"] else 0.0
        breach_rate = d["breached"] / in_progress
        blocked_in_stage = d.get("blocked", 0)
        block_ratio = blocked_in_stage / max(1, d["total"])

        raw_score = avg_days * breach_rate * max(0.01, block_ratio + 0.1)
        scores[stage_name] = raw_score

    # Normalize to [0, 1]
    max_score = max(scores.values()) if scores else 1.0
    if max_score == 0:
        max_score = 1.0

    stage_results = []
    all_stages = []
    for stage_name, raw in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        d = stage_data[stage_name]
        normalized = round(raw / max_score, 4)
        avg_d = round(sum(d["days_list"]) / max(1, len(d["days_list"])), 1)
        b_rate = round(d["breached"] / max(1, d["in_progress"]), 3)
        stage_results.append({
            "stage": stage_name,
            "bottleneck_score": normalized,
            "raw_score": round(raw, 2),
            "total_parcels_in_stage": d["total"],
            "in_progress_count": d["in_progress"],
            "breached_count": d["breached"],
            "avg_days_pending": avg_d,
            "sla_breach_rate": b_rate,
        })
        all_stages.append({
            "stage": stage_name,
            "pending_count": d["in_progress"],
            "avg_days_pending": avg_d,
            "bottleneck_score": normalized,
        })

    # Build primary_bottleneck structured object conforming to frontend contract
    if stage_results and stage_results[0]["in_progress_count"] > 0:
        top_st = stage_results[0]
        primary_bottleneck_obj = {
            "stage": top_st["stage"],
            "pending_count": top_st["in_progress_count"],
            "avg_days_pending": top_st["avg_days_pending"],
            "sla_days": 30,
            "breach_rate": top_st["sla_breach_rate"],
            "impact_description": (
                f"{top_st['stage'].replace('_', ' ').title()} stage is the primary procedural bottleneck "
                f"with {top_st['in_progress_count']} parcels pending and a {round(top_st['sla_breach_rate'] * 100)}% SLA breach rate."
            ),
        }
        primary_bottleneck_name = top_st["stage"]
    else:
        primary_bottleneck_obj = {
            "stage": "SURVEY",
            "pending_count": 0,
            "avg_days_pending": 0.0,
            "sla_days": 30,
            "breach_rate": 0.0,
            "impact_description": "Workflow progressing within statutory benchmarks. No critical bottlenecks detected.",
        }
        primary_bottleneck_name = "SURVEY"

    return {
        "project_id": str(project.project_id),
        "project_name": project.name,
        "primary_bottleneck": primary_bottleneck_obj,
        "primary_bottleneck_name": primary_bottleneck_name,
        "all_stages": all_stages,
        "stages": stage_results,
        "message": "Bottleneck analysis computed successfully.",
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Priority Ranking ──────────────────────────────────────────────────────────

@router.get(
    "/priority/{project_id}",
    summary="Priority score ranking with intervention recommendations per parcel",
    response_model=dict,
)
@router.get(
    "/projects/{project_id}/priority",
    summary="Priority score ranking with intervention recommendations per parcel",
    response_model=dict,
)
def get_project_priority(
    project_id: str,
    top_n: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Rank parcels by priority_score and emit intervention recommendations.

    priority_score = risk_score_normalized × stage_complexity_weight × (1 + dispute_flag) × (1 + sla_breach_flag)
    """
    project = _resolve_analytics_project(db, project_id)
    resolved_id = project.project_id

    today = datetime.now(timezone.utc).date()

    parcels = db.execute(
        select(Parcel).where(
            Parcel.project_id == resolved_id,
            Parcel.status.not_in([ParcelStatus.COMPLETED.value]),
        )
    ).scalars().all()

    parcel_ids = [p.parcel_id for p in parcels]

    # Fetch active stages for SLA info
    stage_map: Dict[UUID, AcquisitionStage] = {}
    if parcel_ids:
        active_stages = db.execute(
            select(AcquisitionStage)
            .where(
                AcquisitionStage.parcel_id.in_(parcel_ids),
                AcquisitionStage.status == StageStatus.IN_PROGRESS.value,
            )
        ).scalars().all()
        for s in active_stages:
            stage_map[s.parcel_id] = s

    # Fetch compensation for pending ratio
    comp_map: Dict[UUID, tuple] = {}
    if parcel_ids:
        comp_rows = db.execute(
            select(Compensation.parcel_id, Compensation.approved_amount, Compensation.paid_amount)
            .where(Compensation.parcel_id.in_(parcel_ids))
        ).all()
        for row in comp_rows:
            comp_map[row[0]] = (float(row[1] or 0), float(row[2] or 0))

    results = []
    for parcel in parcels:
        stage = stage_map.get(parcel.parcel_id)
        comp = comp_map.get(parcel.parcel_id, (0.0, 0.0))

        # Compute priority factors
        risk_norm = parcel.risk_score / 100.0 if parcel.risk_score > 1.0 else parcel.risk_score
        complexity = STAGE_COMPLEXITY_WEIGHTS.get(str(parcel.current_stage), 0.5)
        dispute_flag = 1 if parcel.status in (ParcelStatus.DISPUTED.value, ParcelStatus.BLOCKED.value) else 0
        sla_breach_flag = 0
        days_overdue = 0
        days_pending = 30
        target_val = getattr(stage, "target_date", None) if stage else None
        if target_val:
            target = target_val if hasattr(target_val, "toordinal") else (target_val.date() if hasattr(target_val, "date") else None)
            if target and target < today:
                sla_breach_flag = 1
                days_overdue = (today - target).days

        start_val = getattr(stage, "start_date", None) if stage else None
        if start_val:
            start = start_val if hasattr(start_val, "toordinal") else (start_val.date() if hasattr(start_val, "date") else None)
            if start:
                days_pending = max(1, (today - start).days)
        else:
            days_pending = max(15, days_overdue + 30)

        approved, paid = comp
        comp_pending_ratio = (approved - paid) / max(1.0, approved) if approved > 0 else 0.0

        priority_score = round(
            risk_norm * complexity * (1 + dispute_flag) * (1 + sla_breach_flag),
            4,
        )

        # Intervention recommendations
        interventions = []
        if sla_breach_flag:
            interventions.append({
                "type": "SLA_ESCALATION",
                "message": f"Stage '{parcel.current_stage}' is {days_overdue} day(s) past the statutory deadline. Escalate to district collector.",
            })
        if dispute_flag:
            interventions.append({
                "type": "LEGAL_REVIEW",
                "message": f"Parcel is in {parcel.status} status. Assign legal officer for dispute resolution.",
            })
        if comp_pending_ratio > 0.5:
            interventions.append({
                "type": "COMPENSATION_RELEASE",
                "message": f"{comp_pending_ratio*100:.0f}% of approved compensation is pending disbursement. Initiate payment release.",
            })
        if not interventions:
            interventions.append({
                "type": "MONITOR",
                "message": "No immediate intervention required. Continue standard monitoring.",
            })

        rec_msg = interventions[0]["message"] if interventions else "Continue standard monitoring."
        impact_level = "HIGH" if priority_score >= 0.5 or sla_breach_flag or dispute_flag else ("MEDIUM" if priority_score >= 0.25 else "LOW")

        results.append({
            "parcel_id": str(parcel.parcel_id),
            "survey_number": parcel.survey_number,
            "stage": parcel.current_stage,
            "current_stage": parcel.current_stage,
            "days_pending": days_pending,
            "impact": impact_level,
            "priority_score": priority_score,
            "recommendation": rec_msg,
            "intervention_recommendation": rec_msg,
            "owner_name": parcel.owner_name,
            "district": parcel.district,
            "status": parcel.status,
            "risk_score": parcel.risk_score,
            "stage_complexity": complexity,
            "sla_breached": bool(sla_breach_flag),
            "disputed": bool(dispute_flag),
            "compensation_pending_ratio": round(comp_pending_ratio, 3),
            "intervention_recommendations": interventions,
        })

    results.sort(key=lambda x: x["priority_score"], reverse=True)
    ranked = results[:top_n]

    return {
        "project_id": str(project.project_id),
        "project_name": project.name,
        "total_parcels_ranked": len(results),
        "total_ranked": len(results),
        "parcels": ranked,
        "ranked_parcels": ranked,
        "items": ranked,
        "message": "All parcels in this project are completed or no uncompleted parcels exist." if not results else f"{len(results)} parcels prioritized successfully.",
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Why Delayed ───────────────────────────────────────────────────────────────

@router.get(
    "/parcels/{parcel_id}/why-delayed",
    summary="Structured delay factors for a specific parcel using Phase 4 feature definitions",
    response_model=dict,
)
def get_parcel_why_delayed(
    parcel_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Return human-readable structured delay factors derived from Phase 4 feature definitions.

    Factors analysed:
    1. SLA comparison (days_pending vs statutory target, over_by_days)
    2. Rate trend (processing_rate vs historical baseline, trend direction)
    3. Adjacent disputes (neighboring parcels in DISPUTED/BLOCKED status)
    4. Compensation bottleneck (compensation_pending_ratio with disbursement lag)
    5. Stage complexity (regulatory burden weight for current stage)
    """
    parcel = db.execute(
        select(Parcel).where(Parcel.parcel_id == parcel_id)
    ).scalar_one_or_none()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found.")

    if parcel.status == ParcelStatus.COMPLETED.value or str(parcel.current_stage) == "CLOSURE":
        return {
            "parcel_id": str(parcel_id),
            "survey_number": parcel.survey_number,
            "owner_name": parcel.owner_name,
            "district": parcel.district,
            "current_stage": parcel.current_stage,
            "status": parcel.status,
            "overall_severity": "ok",
            "overall_assessment": "Completed - Acquisition and possession closed successfully.",
            "factors": [],
            "message": "This parcel has completed all acquisition workflow stages and is closed.",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    today = datetime.now(timezone.utc).date()
    factors = []

    # 1. SLA Comparison
    from app.services.sla_service import STAGE_SLA_DAYS, compute_stage_sla
    active_stage = db.execute(
        select(AcquisitionStage).where(
            AcquisitionStage.parcel_id == parcel_id,
            AcquisitionStage.status == StageStatus.IN_PROGRESS.value,
        )
    ).scalar_one_or_none()

    if active_stage:
        sla_info = compute_stage_sla(active_stage)
        statutory_days = STAGE_SLA_DAYS.get(str(active_stage.stage_name), 60)
        days_pending = sla_info["days_pending"]
        days_until = sla_info["days_until_deadline"]
        is_breached = sla_info["is_breached"]
        over_by = abs(days_until) if days_until is not None and days_until < 0 else 0

        if is_breached:
            severity = "critical"
            explanation = (
                f"Stage '{active_stage.stage_name}' has been active for {days_pending} days, "
                f"which is {over_by} day(s) past the {statutory_days}-day statutory SLA. "
                f"This is a confirmed SLA breach requiring immediate escalation."
            )
        elif days_until is not None and days_until <= 7:
            severity = "warning"
            explanation = (
                f"Stage '{active_stage.stage_name}' has been active for {days_pending} days. "
                f"The statutory deadline of {statutory_days} days is breached in {days_until} day(s). "
                f"Action required this week to avoid SLA breach."
            )
        else:
            severity = "ok"
            explanation = (
                f"Stage '{active_stage.stage_name}' has been active for {days_pending} days. "
                f"Statutory SLA is {statutory_days} days; {days_until} day(s) remain."
            )

        factors.append({
            "type": "SLA_COMPARISON",
            "title": "SLA Deadline Status",
            "value": {
                "stage": str(active_stage.stage_name),
                "days_pending": days_pending,
                "statutory_sla_days": statutory_days,
                "days_until_deadline": days_until,
                "over_by_days": over_by,
                "is_breached": is_breached,
            },
            "severity": severity,
            "explanation": explanation,
        })
    else:
        factors.append({
            "type": "SLA_COMPARISON",
            "title": "SLA Deadline Status",
            "value": {"stage": parcel.current_stage, "days_pending": 0, "is_breached": False},
            "severity": "ok",
            "explanation": f"No active in-progress stage found. Current stage: {parcel.current_stage}.",
        })

    # 2. Rate Trend (using ProjectHistory snapshots for this project)
    snapshots = db.execute(
        select(ProjectHistory)
        .where(ProjectHistory.project_id == parcel.project_id)
        .order_by(ProjectHistory.snapshot_date.asc())
    ).scalars().all()

    if len(snapshots) >= 2:
        snap_dicts = [
            {
                "snapshot_date": s.snapshot_date,
                "parcels_completed": s.parcels_completed,
                "parcels_total": s.parcels_total,
                "parcels_in_progress": s.parcels_in_progress,
                "parcels_blocked": getattr(s, "parcels_blocked", getattr(s, "parcels_disputed", 0)),
                "compensation_paid_total": float(s.compensation_paid_total),
                "compensation_pending_total": float(s.compensation_pending_total),
                "stages_snapshot": s.stages_snapshot or {},
                "metadata_json": s.metadata_json or {},
            }
            for s in snapshots
        ]
        features = build_features(snap_dicts)
        processing_rate = features["processing_rate"]
        backlog_trend = features["backlog_trend"]

        if backlog_trend > 0.05 and processing_rate < 0.5:
            rate_severity = "critical"
            rate_explanation = (
                f"Acquisition velocity is critically low at {processing_rate:.2f} parcels/day "
                f"while the backlog is growing at +{backlog_trend:.2f} parcels/day. "
                f"The project is falling further behind schedule."
            )
        elif backlog_trend > 0:
            rate_severity = "warning"
            rate_explanation = (
                f"Processing rate is {processing_rate:.2f} parcels/day but the backlog "
                f"is still expanding (+{backlog_trend:.2f}/day). Moderate deceleration observed."
            )
        else:
            rate_severity = "ok"
            rate_explanation = (
                f"Acquisition velocity ({processing_rate:.2f} parcels/day) is outpacing "
                f"backlog growth ({backlog_trend:.2f}/day). Progress is on track."
            )

        factors.append({
            "type": "RATE_TREND",
            "title": "Acquisition Rate & Backlog Trend",
            "value": {
                "processing_rate_per_day": round(processing_rate, 4),
                "backlog_trend_per_day": round(backlog_trend, 4),
                "snapshot_count": len(snapshots),
            },
            "severity": rate_severity,
            "explanation": rate_explanation,
        })
    else:
        factors.append({
            "type": "RATE_TREND",
            "title": "Acquisition Rate & Backlog Trend",
            "value": {"snapshot_count": len(snapshots)},
            "severity": "ok",
            "explanation": "Insufficient timeline snapshots (< 2) to compute rate trend. Monitoring will improve as more data is captured.",
        })

    # 3. Adjacent Disputes
    adjacent_disputed = db.execute(
        select(func.count(Parcel.parcel_id))
        .where(
            Parcel.project_id == parcel.project_id,
            Parcel.district == parcel.district,
            Parcel.parcel_id != parcel_id,
            Parcel.status.in_([ParcelStatus.DISPUTED.value, ParcelStatus.BLOCKED.value]),
        )
    ).scalar() or 0

    total_adjacent = db.execute(
        select(func.count(Parcel.parcel_id))
        .where(
            Parcel.project_id == parcel.project_id,
            Parcel.district == parcel.district,
            Parcel.parcel_id != parcel_id,
        )
    ).scalar() or 1

    adj_dispute_ratio = adjacent_disputed / total_adjacent

    if adj_dispute_ratio > 0.3:
        adj_severity = "critical"
        adj_explanation = (
            f"{adjacent_disputed} of {total_adjacent} neighboring parcels in {parcel.district} district "
            f"are disputed or blocked ({adj_dispute_ratio*100:.0f}%). Legal proceedings in adjacent parcels "
            f"frequently cause judicial stays and delays in this parcel's acquisition too."
        )
    elif adj_dispute_ratio > 0.1:
        adj_severity = "warning"
        adj_explanation = (
            f"{adjacent_disputed} of {total_adjacent} neighboring parcels in {parcel.district} are in contested status. "
            f"Monitor for spill-over litigation effects."
        )
    else:
        adj_severity = "ok"
        adj_explanation = (
            f"Only {adjacent_disputed} of {total_adjacent} neighboring parcels in {parcel.district} are contested. "
            f"Low litigation spillover risk."
        )

    factors.append({
        "type": "ADJACENT_DISPUTES",
        "title": "Neighboring Parcel Dispute Risk",
        "value": {
            "adjacent_disputed": adjacent_disputed,
            "total_adjacent_in_district": total_adjacent,
            "adjacent_dispute_ratio": round(adj_dispute_ratio, 3),
        },
        "severity": adj_severity,
        "explanation": adj_explanation,
    })

    # 4. Compensation Bottleneck
    comp = db.execute(
        select(Compensation).where(Compensation.parcel_id == parcel_id)
    ).scalar_one_or_none()

    if comp:
        approved = float(comp.approved_amount or 0)
        paid = float(comp.paid_amount or 0)
        pending = max(0.0, approved - paid)
        pending_ratio = pending / max(1.0, approved) if approved > 0 else 0.0

        if pending_ratio > 0.5:
            comp_severity = "critical"
            comp_explanation = (
                f"INR {pending:,.0f} ({pending_ratio*100:.0f}% of approved INR {approved:,.0f}) "
                f"compensation is still pending disbursement. Unpaid compensation is a common "
                f"legal trigger for court-ordered injunctions that block land possession."
            )
        elif pending_ratio > 0.1:
            comp_severity = "warning"
            comp_explanation = (
                f"INR {pending:,.0f} ({pending_ratio*100:.0f}%) remains unpaid. "
                f"Expedite disbursement to prevent legal challenges."
            )
        else:
            comp_severity = "ok"
            comp_explanation = (
                f"Compensation is largely disbursed (only {pending_ratio*100:.0f}% pending). "
                f"No compensation bottleneck detected."
            )

        factors.append({
            "type": "COMPENSATION_BOTTLENECK",
            "title": "Compensation Disbursement Status",
            "value": {
                "assessed_amount": float(comp.assessed_amount or 0),
                "approved_amount": approved,
                "paid_amount": paid,
                "pending_amount": pending,
                "pending_ratio": round(pending_ratio, 3),
                "payment_status": comp.payment_status,
            },
            "severity": comp_severity,
            "explanation": comp_explanation,
        })
    else:
        factors.append({
            "type": "COMPENSATION_BOTTLENECK",
            "title": "Compensation Disbursement Status",
            "value": {"payment_status": "NO_RECORD"},
            "severity": "warning",
            "explanation": "No compensation record found for this parcel. Verify award and compensation calculation have been completed.",
        })

    # 5. Stage Complexity
    complexity_weight = STAGE_COMPLEXITY_WEIGHTS.get(str(parcel.current_stage), 0.5)
    if complexity_weight >= 0.8:
        complexity_severity = "critical"
        complexity_explanation = (
            f"The current stage '{parcel.current_stage}' carries a regulatory complexity weight of "
            f"{complexity_weight:.2f}/1.0 — this is one of the most legally intensive stages "
            f"in the LARR Act 2013 workflow. Delays here are normal but require active management."
        )
    elif complexity_weight >= 0.5:
        complexity_severity = "warning"
        complexity_explanation = (
            f"Stage '{parcel.current_stage}' has moderate regulatory complexity ({complexity_weight:.2f}/1.0). "
            f"Procedural compliance checks are required at each milestone."
        )
    else:
        complexity_severity = "ok"
        complexity_explanation = (
            f"Stage '{parcel.current_stage}' is relatively low-complexity ({complexity_weight:.2f}/1.0). "
            f"Standard administrative processing should proceed without major obstacles."
        )

    factors.append({
        "type": "STAGE_COMPLEXITY",
        "title": "Regulatory Stage Complexity",
        "value": {
            "current_stage": parcel.current_stage,
            "complexity_weight": complexity_weight,
            "complexity_scale": "0.0 (simple) to 1.0 (most complex)",
        },
        "severity": complexity_severity,
        "explanation": complexity_explanation,
    })

    # Overall severity rollup
    severity_rank = {"ok": 0, "warning": 1, "critical": 2}
    max_severity = max(factors, key=lambda f: severity_rank.get(f["severity"], 0))["severity"]

    return {
        "parcel_id": str(parcel_id),
        "survey_number": parcel.survey_number,
        "owner_name": parcel.owner_name,
        "district": parcel.district,
        "current_stage": parcel.current_stage,
        "status": parcel.status,
        "overall_severity": max_severity,
        "factors": factors,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
