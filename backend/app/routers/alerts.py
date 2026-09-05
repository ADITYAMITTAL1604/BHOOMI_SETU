"""FastAPI router for /alerts — alert listing, creation, and mark-read endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, update, or_, and_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_central_or_above, filter_by_geographic_scope, get_user_geographic_scope
from app.database import get_db
from app.models import Alert, User, Project, Parcel
from app.models.enums import AlertSeverity, UserRole
from app.utils.pagination import create_page_response

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class AlertCreateRequest(BaseModel):
    title: str
    message: str
    severity: str = AlertSeverity.INFO.value
    target_user_id: Optional[UUID] = None
    target_role: Optional[str] = None  # broadcast to all users with this role
    project_id: Optional[UUID] = None
    parcel_id: Optional[UUID] = None
    metadata: Optional[dict] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "",
    summary="List alerts for the current user",
    response_model=dict,
)
def list_alerts(
    is_read: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    project_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return paginated alerts for the authenticated user with unread count in meta.

    Alerts are always constrained to the user's geographic scope (state/district),
    even when the alert is addressed directly to the user (Alert.user_id match).
    A user should never see — and then be unable to open — an alert for a
    project/parcel outside their jurisdiction.
    """
    stmt = select(Alert).outerjoin(Project, Alert.project_id == Project.project_id)
    stmt = stmt.where(or_(Alert.user_id == current_user.id, Alert.user_id.is_(None)))

    scope = get_user_geographic_scope(current_user)
    if scope:
        # An alert is visible if:
        #   - it has no project/parcel attached (system-wide notice), OR
        #   - its project is within the user's state/district scope, OR
        #   - its parcel is within the user's state/district scope
        # This applies uniformly whether the alert was broadcast or sent directly
        # to this user — being the addressee does not bypass jurisdiction.
        no_location = and_(Alert.project_id.is_(None), Alert.parcel_id.is_(None))

        project_scope_conditions = filter_by_geographic_scope(current_user, Project)
        parcel_scope_conditions = filter_by_geographic_scope(current_user, Parcel)

        in_scope_clauses = [no_location]
        if project_scope_conditions:
            in_scope_clauses.append(and_(Alert.project_id.isnot(None), *project_scope_conditions))
        if parcel_scope_conditions:
            stmt = stmt.outerjoin(Parcel, Alert.parcel_id == Parcel.parcel_id)
            in_scope_clauses.append(and_(Alert.parcel_id.isnot(None), *parcel_scope_conditions))

        stmt = stmt.where(or_(*in_scope_clauses))

    if is_read is not None:
        stmt = stmt.where(Alert.is_read == is_read)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if project_id:
        stmt = stmt.where(Alert.project_id == project_id)

    stmt = stmt.order_by(Alert.created_at.desc())

    total = db.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar() or 0

    offset = (page - 1) * page_size
    alerts = db.execute(stmt.offset(offset).limit(page_size)).scalars().all()

    unread_count = db.execute(
        select(func.count(Alert.alert_id)).where(
            Alert.user_id == current_user.id,
            Alert.is_read == False,  # noqa: E712
        )
    ).scalar() or 0

    return {
        "items": [_serialize_alert(a) for a in alerts],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, -(-total // page_size)),
        },
        "unread_count": unread_count,
    }


@router.get(
    "/unread-count",
    summary="Get unread alert count for the current user",
    response_model=dict,
)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Lightweight endpoint for notification badge count."""
    count = db.execute(
        select(func.count(Alert.alert_id)).where(
            Alert.user_id == current_user.id,
            Alert.is_read == False,  # noqa: E712
        )
    ).scalar() or 0
    return {"unread_count": count}


@router.post(
    "",
    summary="Create an alert manually (admin/central only)",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def create_alert_endpoint(
    body: AlertCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_central_or_above),
) -> dict:
    """Create an alert targeted to a specific user or broadcast to a role."""
    if body.target_user_id is None and body.target_role is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either target_user_id or target_role must be specified.",
        )

    from app.services.alert_service import create_alert, broadcast_alert

    created_count = 0

    if body.target_user_id:
        alert = create_alert(
            db,
            user_id=body.target_user_id,
            title=body.title,
            message=body.message,
            severity=body.severity,
            project_id=body.project_id,
            parcel_id=body.parcel_id,
            metadata=body.metadata,
        )
        db.commit()
        db.refresh(alert)
        return {"created": 1, "alert": _serialize_alert(alert)}

    if body.target_role:
        created_count = broadcast_alert(
            db,
            role=body.target_role,
            title=body.title,
            message=body.message,
            severity=body.severity,
            project_id=body.project_id,
            parcel_id=body.parcel_id,
            metadata=body.metadata,
        )
        db.commit()
        return {"created": created_count, "broadcast_role": body.target_role}


@router.put(
    "/{alert_id}/read",
    summary="Mark a single alert as read",
    response_model=dict,
)
def mark_alert_read(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Mark a specific alert as read. Only the owning user can mark their own alerts."""
    alert = db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    ).scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

    if alert.user_id != current_user.id and current_user.role not in (
        UserRole.ADMIN.value, UserRole.CENTRAL.value
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your alert.")

    if not alert.is_read:
        alert.is_read = True
        alert.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)

    return _serialize_alert(alert)


@router.put(
    "/read-all",
    summary="Mark all unread alerts for current user as read",
    response_model=dict,
)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Bulk mark all unread alerts for the authenticated user as read."""
    now = datetime.now(timezone.utc)
    result = db.execute(
        update(Alert)
        .where(Alert.user_id == current_user.id, Alert.is_read == False)  # noqa: E712
        .values(is_read=True, read_at=now)
    )
    db.commit()
    return {
        "marked_read": result.rowcount,
        "message": f"Marked {result.rowcount} alert(s) as read.",
    }


# ── Serializer ────────────────────────────────────────────────────────────────

def _serialize_alert(a: Alert) -> dict:
    meta = a.metadata_json or {}
    project_name = meta.get("project_name")
    if not project_name and a.project:
        project_name = a.project.name
    return {
        "alert_id": str(a.alert_id),
        "user_id": str(a.user_id) if a.user_id else None,
        "project_id": str(a.project_id) if a.project_id else None,
        "parcel_id": str(a.parcel_id) if a.parcel_id else None,
        "title": a.title,
        "message": a.message,
        "severity": a.severity,
        "is_read": a.is_read,
        "read_at": a.read_at.isoformat() if a.read_at else None,
        "metadata": a.metadata_json,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "project_name": project_name or "Uttar Pradesh Corridors",
        "issue_type": meta.get("issue_type") or a.title,
        "time_ago": meta.get("time_ago") or "Active",
    }
