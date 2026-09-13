"""SQLAlchemy ORM model for Notification — in-app notification center."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, JSON
from app.models.types import PlatformUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AlertSeverity, NotificationCategory


class Notification(Base):
    __tablename__ = "notifications"

    notification_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False,
        default=AlertSeverity.INFO.value, index=True
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False,
        default=NotificationCategory.SYSTEM.value, index=True
    )
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(PlatformUUID, nullable=True)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", backref="notifications")


# Indexes for notification queries
Index("idx_notif_user_read", Notification.user_id, Notification.is_read)
Index("idx_notif_user_created", Notification.user_id, Notification.created_at.desc())
Index("idx_notif_category", Notification.category, Notification.created_at.desc())
Index("idx_notif_entity", Notification.entity_type, Notification.entity_id)
