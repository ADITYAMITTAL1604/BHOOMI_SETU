"""BhoomiSetu Notification Service — centralized notification dispatch with provider interface."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.enums import AlertSeverity, NotificationCategory

logger = logging.getLogger(__name__)


# ── Provider Interface (future SMS/Email/Push) ───────────────────────────────

class NotificationProvider:
    """Base class for notification delivery providers.

    Subclass this and implement `send()` to add SMS, Email, Push, etc.
    Register providers via `register_provider()`.
    """

    def send(self, user_id: UUID, title: str, message: str, **kwargs) -> bool:
        """Deliver the notification. Return True on success."""
        raise NotImplementedError


class InAppProvider(NotificationProvider):
    """Default in-app notification provider — writes to the notifications table."""

    def send(self, user_id: UUID, title: str, message: str, **kwargs) -> bool:
        # In-app is handled by create_notification directly; this is a no-op hook
        return True


# Provider registry
_providers: list[NotificationProvider] = [InAppProvider()]


def register_provider(provider: NotificationProvider) -> None:
    """Register an additional notification provider (e.g., SMS, Email)."""
    _providers.append(provider)
    logger.info("Registered notification provider: %s", type(provider).__name__)


# ── Core Functions ───────────────────────────────────────────────────────────

def create_notification(
    db: Session,
    *,
    user_id: UUID,
    title: str,
    message: str,
    severity: str = AlertSeverity.INFO.value,
    category: str = NotificationCategory.SYSTEM.value,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    action_url: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Notification:
    """Create and persist a single notification."""
    notif = Notification(
        notification_id=uuid.uuid4(),
        user_id=user_id,
        title=title,
        message=message,
        severity=severity,
        category=category,
        is_read=False,
        entity_type=entity_type,
        entity_id=entity_id,
        action_url=action_url,
        metadata_json=metadata or {},
    )
    db.add(notif)

    # Dispatch to additional providers (future: SMS, Email)
    for provider in _providers[1:]:  # Skip InAppProvider (index 0)
        try:
            provider.send(
                user_id=user_id,
                title=title,
                message=message,
                severity=severity,
                category=category,
            )
        except Exception:
            logger.exception(
                "Provider %s failed for notification to user %s",
                type(provider).__name__, user_id,
            )

    return notif


def get_notifications(
    db: Session,
    user_id: UUID,
    *,
    is_read: Optional[bool] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Return paginated notifications for a user."""
    stmt = select(Notification).where(Notification.user_id == user_id)

    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
    if category:
        stmt = stmt.where(Notification.category == category)
    if severity:
        stmt = stmt.where(Notification.severity == severity)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    stmt = stmt.order_by(Notification.created_at.desc())
    offset = (page - 1) * page_size
    notifs = db.execute(stmt.offset(offset).limit(page_size)).scalars().all()

    return {
        "items": [_notif_to_dict(n) for n in notifs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "unread_count": get_unread_count(db, user_id),
    }


def get_unread_count(db: Session, user_id: UUID) -> int:
    """Return count of unread notifications for a user."""
    return db.execute(
        select(func.count(Notification.notification_id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
    ).scalar() or 0


def mark_as_read(db: Session, notification_id: UUID, user_id: UUID) -> Optional[dict]:
    """Mark a single notification as read."""
    notif = db.execute(
        select(Notification).where(
            Notification.notification_id == notification_id,
            Notification.user_id == user_id,
        )
    ).scalar_one_or_none()

    if not notif:
        return None

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notif)
    return _notif_to_dict(notif)


def mark_all_as_read(db: Session, user_id: UUID) -> int:
    """Mark all unread notifications as read for a user. Returns count updated."""
    now = datetime.now(timezone.utc)
    result = db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True, read_at=now)
    )
    db.commit()
    return result.rowcount


# ── Private helpers ──────────────────────────────────────────────────────────

def _notif_to_dict(n: Notification) -> dict:
    return {
        "notification_id": str(n.notification_id),
        "user_id": str(n.user_id),
        "title": n.title,
        "message": n.message,
        "severity": n.severity,
        "category": n.category,
        "is_read": n.is_read,
        "read_at": n.read_at.isoformat() if n.read_at else None,
        "entity_type": n.entity_type,
        "entity_id": str(n.entity_id) if n.entity_id else None,
        "action_url": n.action_url,
        "metadata": n.metadata_json,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }
