"""SQLAlchemy ORM model for ProjectHistory (timeline snapshots)."""

from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from typing import Optional
from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import PlatformUUID


class ProjectHistory(Base):
    __tablename__ = "project_history"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )

    @property
    def history_id(self) -> uuid.UUID:
        return self.snapshot_id
    project_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    land_required_ha: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    land_acquired_ha: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    parcels_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parcels_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parcels_in_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parcels_disputed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    @property
    def parcels_blocked(self) -> int:
        return self.parcels_disputed

    compensation_paid_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    compensation_pending_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stages_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="history_snapshots")


Index("idx_history_project_date", ProjectHistory.project_id, ProjectHistory.snapshot_date.desc())