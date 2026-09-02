"""Stage transition service — validates workflow transitions, writes audit log, checks SLA."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import StageName, StageStatus, ParcelStatus
from app.models.stage import AcquisitionStage
from app.models.audit_log import AuditLog
from app.models.parcel import Parcel


# ── Stage ordering ─────────────────────────────────────────────────────────────

STAGE_ORDER: list[StageName] = [
    StageName.PROPOSAL,
    StageName.IDENTIFICATION,
    StageName.SURVEY,
    StageName.VERIFICATION,
    StageName.NOTIFICATION,
    StageName.OBJECTION,
    StageName.AWARD,
    StageName.COMPENSATION,
    StageName.REHABILITATION_RESETTLEMENT,
    StageName.POSSESSION,
    StageName.CLOSURE,
]

STAGE_INDEX: dict[str, int] = {s.value: i for i, s in enumerate(STAGE_ORDER)}

# SLA limits per stage in days (TRD §3.3 — approximate regulatory timelines)
STAGE_SLA_DAYS: dict[str, int] = {
    StageName.PROPOSAL.value: 30,
    StageName.IDENTIFICATION.value: 60,
    StageName.SURVEY.value: 90,
    StageName.VERIFICATION.value: 45,
    StageName.NOTIFICATION.value: 30,
    StageName.OBJECTION.value: 60,
    StageName.AWARD.value: 90,
    StageName.COMPENSATION.value: 60,
    StageName.REHABILITATION_RESETTLEMENT.value: 180,
    StageName.POSSESSION.value: 30,
    StageName.CLOSURE.value: 30,
}

# Allowed transitions:
#   - Forward progression (current → next in order)
#   - BLOCKED ↔ IN_PROGRESS status change (same stage, handled separately)
#   - ADMIN / STATE can skip one stage forward
def get_allowed_target_stages(current_stage: str) -> list[str]:
    """Return list of valid target stage values from a given current stage."""
    idx = STAGE_INDEX.get(current_stage)
    if idx is None:
        return []

    allowed = []
    # Forward: next stage
    if idx + 1 < len(STAGE_ORDER):
        allowed.append(STAGE_ORDER[idx + 1].value)
    # Forward skip: skip one (e.g. PROPOSAL → SURVEY) — requires elevated role
    # (checked in endpoint, not here)
    if idx + 2 < len(STAGE_ORDER):
        allowed.append(STAGE_ORDER[idx + 2].value)
    # Backward rollback: go back one stage (re-open)
    if idx - 1 >= 0:
        allowed.append(STAGE_ORDER[idx - 1].value)
    # Self-transition (used to mark as BLOCKED/IN_PROGRESS without stage change)
    allowed.append(current_stage)
    return allowed


# ── Validation ─────────────────────────────────────────────────────────────────

def validate_transition(current_stage: str, target_stage: str) -> None:
    """Raise HTTPException(422) if the transition is not allowed."""
    if current_stage not in STAGE_INDEX:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown current stage: '{current_stage}'",
        )
    if target_stage not in STAGE_INDEX:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown target stage: '{target_stage}'",
        )

    allowed = get_allowed_target_stages(current_stage)
    if target_stage not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Transition from '{current_stage}' to '{target_stage}' is not allowed. "
                f"Allowed targets: {allowed}"
            ),
        )


# ── SLA helpers ────────────────────────────────────────────────────────────────

def compute_sla_breach(stage: AcquisitionStage) -> bool:
    """Return True if the stage has exceeded its target date (SLA breach)."""
    if stage.completion_date:
        return False  # Already completed, no breach
    if stage.target_date:
        now = datetime.now(timezone.utc).date()
        return now > stage.target_date
    # No target date set — not breached
    return False


def get_sla_status(stage: AcquisitionStage) -> dict:
    """Return a dict with SLA info for a stage."""
    breached = compute_sla_breach(stage)
    days_elapsed = None
    days_remaining = None

    if stage.start_date:
        now = datetime.now(timezone.utc).date()
        days_elapsed = (now - stage.start_date).days

    if stage.target_date:
        now = datetime.now(timezone.utc).date()
        days_remaining = (stage.target_date - now).days

    return {
        "breached": breached,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "target_date": stage.target_date.isoformat() if stage.target_date else None,
        "completion_date": stage.completion_date.isoformat() if stage.completion_date else None,
    }


# ── Audit logging ──────────────────────────────────────────────────────────────

def write_transition_audit(
    db: Session,
    user,
    parcel: Parcel,
    old_stage: str,
    new_stage: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    remarks: Optional[str] = None,
) -> AuditLog:
    """Insert an immutable audit log entry for a stage transition."""
    log = AuditLog(
        log_id=uuid.uuid4(),
        user_id=user.id,
        action="STAGE_TRANSITION",
        entity_type="parcel",
        entity_id=parcel.parcel_id,
        old_values={"stage": old_stage},
        new_values={"stage": new_stage, "remarks": remarks},
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    return log


# ── Transition executor ────────────────────────────────────────────────────────

def execute_transition(
    db: Session,
    parcel: Parcel,
    target_stage: str,
    acting_user,
    new_status: Optional[str] = None,
    remarks: Optional[str] = None,
    sla_target_date=None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> dict:
    """
    Execute a stage transition on a parcel:
    1. Validate the transition.
    2. Complete the current AcquisitionStage row.
    3. Activate (or create) the target AcquisitionStage row.
    4. Update Parcel.current_stage and Parcel.status.
    5. Write audit log.
    6. Return SLA info.
    """
    old_stage = parcel.current_stage
    validate_transition(old_stage, target_stage)

    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()

    # Mark the OLD stage as COMPLETED (if it exists and is not a self-transition)
    if old_stage != target_stage:
        old_stage_row = db.execute(
            select(AcquisitionStage).where(
                AcquisitionStage.parcel_id == parcel.parcel_id,
                AcquisitionStage.stage_name == old_stage,
            )
        ).scalar_one_or_none()

        if old_stage_row and old_stage_row.status != StageStatus.COMPLETED.value:
            old_stage_row.status = StageStatus.COMPLETED.value
            old_stage_row.completion_date = today

    # Find or create the TARGET stage row
    target_stage_row = db.execute(
        select(AcquisitionStage).where(
            AcquisitionStage.parcel_id == parcel.parcel_id,
            AcquisitionStage.stage_name == target_stage,
        )
    ).scalar_one_or_none()

    target_idx = STAGE_INDEX[target_stage]

    if target_stage_row is None:
        # Create it
        target_stage_row = AcquisitionStage(
            stage_id=uuid.uuid4(),
            parcel_id=parcel.parcel_id,
            stage_name=target_stage,
            stage_order=target_idx + 1,
            start_date=today,
            target_date=sla_target_date,
            status=StageStatus.IN_PROGRESS.value,
            assigned_officer=parcel.assigned_officer,
            remarks=remarks,
        )
        db.add(target_stage_row)
    else:
        # Update existing
        target_stage_row.status = StageStatus.IN_PROGRESS.value
        target_stage_row.start_date = target_stage_row.start_date or today
        if sla_target_date:
            target_stage_row.target_date = sla_target_date
        if remarks:
            target_stage_row.remarks = remarks

    # Update parcel fields
    parcel.current_stage = target_stage
    parcel.updated_at = now_utc

    # Determine new parcel status
    if new_status:
        parcel.status = new_status
    elif target_stage == StageName.CLOSURE.value:
        parcel.status = ParcelStatus.COMPLETED.value
    elif target_stage == StageName.PROPOSAL.value:
        parcel.status = ParcelStatus.NOT_STARTED.value
    else:
        parcel.status = ParcelStatus.IN_PROGRESS.value

    # Write audit log
    write_transition_audit(
        db=db,
        user=acting_user,
        parcel=parcel,
        old_stage=old_stage,
        new_stage=target_stage,
        ip_address=ip_address,
        user_agent=user_agent,
        remarks=remarks,
    )

    # Alert hooks
    sla_info = get_sla_status(target_stage_row)
    try:
        from app.services.alert_service import create_stage_completion_alert, create_sla_breach_alert
        if old_stage != target_stage and 'old_stage_row' in locals() and old_stage_row:
            create_stage_completion_alert(
                db=db,
                parcel=parcel,
                stage=old_stage_row,
                actor_user_id=acting_user.id if hasattr(acting_user, 'id') else None,
                next_stage_name=target_stage,
            )
        if sla_info.get("is_breached"):
            create_sla_breach_alert(db=db, parcel=parcel, stage=target_stage_row)
    except Exception as exc:
        pass

    db.commit()
    db.refresh(parcel)
    db.refresh(target_stage_row)

    return {
        "parcel_id": str(parcel.parcel_id),
        "old_stage": old_stage,
        "new_stage": target_stage,
        "parcel_status": parcel.status,
        "sla": sla_info,
        "remarks": remarks,
        "transitioned_by": str(acting_user.id) if hasattr(acting_user, 'id') else None,
        "transitioned_at": now_utc.isoformat(),
    }
