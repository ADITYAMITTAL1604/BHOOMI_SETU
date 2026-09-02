"""BhoomiSetu SLA Service — per-stage timer, breach detection, and sweep utilities."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import AcquisitionStage, Alert, AuditLog, Parcel
from app.models.enums import ParcelStatus, StageStatus

logger = logging.getLogger(__name__)

# Statutory SLA days per stage (calendar days from stage start)
STAGE_SLA_DAYS: Dict[str, int] = {
    "PROPOSAL": 30,
    "IDENTIFICATION": 45,
    "SURVEY": 60,
    "VERIFICATION": 30,
    "NOTIFICATION": 30,
    "OBJECTION": 90,
    "AWARD": 60,
    "COMPENSATION": 45,
    "REHABILITATION_RESETTLEMENT": 120,
    "POSSESSION": 30,
    "CLOSURE": 15,
}


def compute_stage_sla(stage: AcquisitionStage) -> Dict[str, Any]:
    """Compute SLA timer fields for a single AcquisitionStage.

    Returns
    -------
    dict with keys:
        - stage_id: str
        - stage_name: str
        - status: str
        - start_date: date | None
        - target_date: date | None
        - days_pending: int  (days since start; 0 if not started)
        - statutory_sla_days: int
        - days_until_deadline: int | None  (negative = overdue)
        - is_breached: bool
        - breach_severity: 'ok' | 'warning' | 'critical'
    """
    today = datetime.now(timezone.utc).date()
    sla_days = STAGE_SLA_DAYS.get(str(stage.stage_name), 60)

    start = stage.start_date if isinstance(stage.start_date, date) else (
        stage.start_date.date() if hasattr(stage.start_date, "date") else None
    )
    target = stage.target_date if isinstance(stage.target_date, date) else (
        stage.target_date.date() if hasattr(stage.target_date, "date") else None
    )

    # days_pending: how many calendar days since stage started
    days_pending = (today - start).days if start else 0

    # Compute days_until_deadline using target_date or derived from start
    if target:
        days_until_deadline = (target - today).days
    elif start:
        deadline = date.fromordinal(start.toordinal() + sla_days)
        days_until_deadline = (deadline - today).days
    else:
        days_until_deadline = None

    # A stage is breached if:
    # - status is IN_PROGRESS and past target date
    # - or target date is explicitly set and today >= target_date
    is_breached = False
    if stage.status == StageStatus.IN_PROGRESS.value:
        if days_until_deadline is not None and days_until_deadline < 0:
            is_breached = True

    # Severity tiers
    if not is_breached:
        if days_until_deadline is not None and days_until_deadline <= 7:
            breach_severity = "warning"
        else:
            breach_severity = "ok"
    else:
        overdue_days = abs(days_until_deadline) if days_until_deadline is not None else 0
        breach_severity = "critical" if overdue_days > 14 else "warning"

    return {
        "stage_id": str(stage.stage_id),
        "stage_name": str(stage.stage_name),
        "status": str(stage.status),
        "start_date": start.isoformat() if start else None,
        "target_date": target.isoformat() if target else None,
        "days_pending": max(0, days_pending),
        "statutory_sla_days": sla_days,
        "days_until_deadline": days_until_deadline,
        "is_breached": is_breached,
        "breach_severity": breach_severity,
    }


def run_sla_sweep(
    db: Session,
    project_id: Optional[UUID] = None,
    create_alerts: bool = True,
) -> Dict[str, Any]:
    """Sweep all IN_PROGRESS stages, detect SLA breaches, update parcel statuses.

    For each newly breached stage:
    - Sets parcel.status = BLOCKED (if not already COMPLETED or DISPUTED)
    - Optionally creates an Alert record
    - Writes an AuditLog entry

    Returns summary dict with breach_count, updated_parcel_count.
    """
    today = datetime.now(timezone.utc).date()

    # Query in-progress stages that have a target_date and are past it
    stmt = (
        select(AcquisitionStage)
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(
            AcquisitionStage.status == StageStatus.IN_PROGRESS.value,
            AcquisitionStage.target_date.isnot(None),
            AcquisitionStage.target_date < today,
        )
    )
    if project_id:
        stmt = stmt.where(Parcel.project_id == project_id)

    breached_stages = db.execute(stmt).scalars().all()

    breach_count = len(breached_stages)
    updated_parcels: set[UUID] = set()
    alerts_created = 0

    for stage in breached_stages:
        parcel = db.execute(
            select(Parcel).where(Parcel.parcel_id == stage.parcel_id)
        ).scalar_one_or_none()

        if not parcel:
            continue

        # Auto-update parcel.status → BLOCKED if currently IN_PROGRESS
        if parcel.status == ParcelStatus.IN_PROGRESS.value:
            parcel.status = ParcelStatus.BLOCKED.value
            updated_parcels.add(parcel.parcel_id)

            # Audit log
            audit = AuditLog(
                action="SLA_BREACH_AUTO_BLOCK",
                entity_type="parcel",
                entity_id=parcel.parcel_id,
                old_values={"status": ParcelStatus.IN_PROGRESS.value},
                new_values={
                    "status": ParcelStatus.BLOCKED.value,
                    "reason": f"SLA breached on stage {stage.stage_name}",
                    "stage_id": str(stage.stage_id),
                    "days_overdue": (today - stage.target_date).days if stage.target_date else 0,
                },
            )
            db.add(audit)

            if create_alerts:
                from app.services.alert_service import create_sla_breach_alert
                try:
                    create_sla_breach_alert(db, parcel, stage)
                    alerts_created += 1
                except Exception as exc:
                    logger.warning("Could not create SLA breach alert: %s", exc)

    if updated_parcels:
        db.commit()
        logger.info(
            "SLA sweep: %d breaches found, %d parcels set to BLOCKED.",
            breach_count,
            len(updated_parcels),
        )

    return {
        "breach_count": breach_count,
        "updated_parcel_count": len(updated_parcels),
        "alerts_created": alerts_created,
    }


def get_project_sla_summary(
    db: Session, project_id: UUID
) -> List[Dict[str, Any]]:
    """Return SLA status for all IN_PROGRESS stages under a project."""
    stmt = (
        select(AcquisitionStage, Parcel.survey_number, Parcel.district)
        .join(Parcel, Parcel.parcel_id == AcquisitionStage.parcel_id)
        .where(
            Parcel.project_id == project_id,
            AcquisitionStage.status == StageStatus.IN_PROGRESS.value,
        )
        .order_by(AcquisitionStage.target_date.asc().nulls_last())
    )
    rows = db.execute(stmt).all()

    result = []
    for stage, survey_number, district in rows:
        sla = compute_stage_sla(stage)
        sla["survey_number"] = survey_number
        sla["district"] = district
        sla["parcel_id"] = str(stage.parcel_id)
        result.append(sla)
    return result
