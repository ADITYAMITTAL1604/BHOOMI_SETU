"""BhoomiSetu Alert Service — centralized alert creation and broadcast utilities."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, AcquisitionStage, Parcel, User
from app.models.enums import AlertSeverity, UserRole

logger = logging.getLogger(__name__)


def create_alert(
    db: Session,
    *,
    user_id: Optional[UUID],
    title: str,
    message: str,
    severity: str = AlertSeverity.INFO.value,
    project_id: Optional[UUID] = None,
    parcel_id: Optional[UUID] = None,
    metadata: Optional[dict] = None,
) -> Alert:
    """Create and persist a single Alert record."""
    alert = Alert(
        user_id=user_id,
        project_id=project_id,
        parcel_id=parcel_id,
        title=title,
        message=message,
        severity=severity,
        is_read=False,
        metadata_json=metadata or {},
    )
    db.add(alert)
    # Caller is responsible for commit
    return alert


def broadcast_alert(
    db: Session,
    *,
    role: str,
    title: str,
    message: str,
    severity: str = AlertSeverity.WARNING.value,
    project_id: Optional[UUID] = None,
    parcel_id: Optional[UUID] = None,
    metadata: Optional[dict] = None,
) -> int:
    """Fan-out an alert to all active users with the given role.

    Returns the number of alert records created.
    """
    users = db.execute(
        select(User).where(User.role == role, User.is_active == True)  # noqa: E712
    ).scalars().all()

    count = 0
    for user in users:
        create_alert(
            db,
            user_id=user.id,
            title=title,
            message=message,
            severity=severity,
            project_id=project_id,
            parcel_id=parcel_id,
            metadata=metadata,
        )
        count += 1

    logger.info("broadcast_alert: created %d alerts for role=%s", count, role)
    return count


def create_sla_breach_alert(
    db: Session,
    parcel: Parcel,
    stage: AcquisitionStage,
) -> None:
    """Create an SLA breach alert targeted to the assigned officer and district-level users."""
    from app.services.sla_service import STAGE_SLA_DAYS
    from datetime import date

    today = datetime.now(timezone.utc).date()
    target = stage.target_date
    if isinstance(target, datetime):
        target = target.date()
    days_overdue = (today - target).days if target else 0
    sla_days = STAGE_SLA_DAYS.get(str(stage.stage_name), 60)

    title = f"SLA Breach: {stage.stage_name} on Parcel {parcel.survey_number}"
    message = (
        f"Parcel {parcel.survey_number} ({parcel.district}) has exceeded the "
        f"{sla_days}-day statutory SLA for stage '{stage.stage_name}' by {days_overdue} day(s). "
        f"Parcel status has been automatically set to BLOCKED."
    )
    meta = {
        "stage_name": str(stage.stage_name),
        "stage_id": str(stage.stage_id),
        "days_overdue": days_overdue,
        "statutory_sla_days": sla_days,
        "survey_number": parcel.survey_number,
        "district": parcel.district,
    }

    # Notify the assigned officer if set
    if stage.assigned_officer:
        create_alert(
            db,
            user_id=stage.assigned_officer,
            title=title,
            message=message,
            severity=AlertSeverity.CRITICAL.value,
            project_id=parcel.project_id,
            parcel_id=parcel.parcel_id,
            metadata=meta,
        )

    # Also broadcast to all DISTRICT and STATE users
    for role in (UserRole.DISTRICT.value, UserRole.STATE.value):
        broadcast_alert(
            db,
            role=role,
            title=title,
            message=message,
            severity=AlertSeverity.CRITICAL.value,
            project_id=parcel.project_id,
            parcel_id=parcel.parcel_id,
            metadata=meta,
        )


def create_stage_completion_alert(
    db: Session,
    parcel: Parcel,
    stage: AcquisitionStage,
    actor_user_id: Optional[UUID] = None,
    next_stage_name: Optional[str] = None,
) -> None:
    """Create a stage-completion notification for the assigned officer and project agency."""
    title = f"Stage Complete: {stage.stage_name} — {parcel.survey_number}"
    next_info = f" Proceeding to '{next_stage_name}'." if next_stage_name else ""
    message = (
        f"Stage '{stage.stage_name}' for parcel {parcel.survey_number} "
        f"({parcel.district}, {parcel.state}) has been marked as completed.{next_info}"
    )
    meta = {
        "stage_name": str(stage.stage_name),
        "stage_id": str(stage.stage_id),
        "next_stage": next_stage_name,
        "completed_by": str(actor_user_id) if actor_user_id else None,
    }

    # Notify the assigned officer
    if stage.assigned_officer:
        create_alert(
            db,
            user_id=stage.assigned_officer,
            title=title,
            message=message,
            severity=AlertSeverity.INFO.value,
            project_id=parcel.project_id,
            parcel_id=parcel.parcel_id,
            metadata=meta,
        )

    # Notify the actor (if different from assigned officer)
    if actor_user_id and actor_user_id != stage.assigned_officer:
        create_alert(
            db,
            user_id=actor_user_id,
            title=title,
            message=message,
            severity=AlertSeverity.INFO.value,
            project_id=parcel.project_id,
            parcel_id=parcel.parcel_id,
            metadata=meta,
        )
