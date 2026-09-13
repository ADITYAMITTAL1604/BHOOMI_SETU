"""FastAPI router for /notifications — in-app notification center endpoints."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.services.notification_service import (
    get_notifications,
    get_unread_count,
    mark_all_as_read,
    mark_as_read,
)

router = APIRouter()


@router.get(
    "",
    summary="List notifications for current user",
    response_model=dict,
)
def list_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    category: Optional[str] = Query(None, description="Filter by category (approval, sla, document, stage, system)"),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, WARNING, CRITICAL)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return paginated notifications for the authenticated user."""
    return get_notifications(
        db, current_user.id,
        is_read=is_read,
        category=category,
        severity=severity,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/unread-count",
    summary="Get unread notification count",
    response_model=dict,
)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return the count of unread notifications for the authenticated user."""
    count = get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.put(
    "/{notification_id}/read",
    summary="Mark a notification as read",
    response_model=dict,
)
def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Mark a single notification as read."""
    result = mark_as_read(db, notification_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return result


@router.put(
    "/read-all",
    summary="Mark all notifications as read",
    response_model=dict,
)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Mark all unread notifications as read for the authenticated user."""
    count = mark_all_as_read(db, current_user.id)
    return {"message": f"Marked {count} notifications as read.", "updated_count": count}
