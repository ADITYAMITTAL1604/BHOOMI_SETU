"""SQLAlchemy ORM model for Alert (ERD §3.1)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, JSON
from app.models.types import PlatformUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AlertSeverity


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PlatformUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PlatformUUID, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=True, index=True
    )
    parcel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PlatformUUID, ForeignKey("parcels.parcel_id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default=AlertSeverity.INFO.value, index=True)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="alerts")
    project = relationship("Project", backref="alerts")
    parcel = relationship("Parcel", backref="alerts")


Index("idx_alert_user_read", Alert.user_id, Alert.is_read)
Index("idx_alert_project", Alert.project_id)
Index("idx_alert_parcel", Alert.parcel_id)
Index("idx_alert_severity_created", Alert.severity, Alert.created_at.desc())