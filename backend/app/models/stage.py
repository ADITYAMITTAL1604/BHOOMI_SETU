"""SQLAlchemy ORM model for AcquisitionStage."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text
from app.models.types import PlatformUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import StageName, StageStatus


class AcquisitionStage(Base):
    __tablename__ = "acquisition_stages"

    stage_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, ForeignKey("parcels.parcel_id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=StageStatus.NOT_STARTED.value, index=True
    )
    assigned_officer: Mapped[Optional[uuid.UUID]] = mapped_column(
        PlatformUUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    parcel = relationship("Parcel", back_populates="stages")


Index("idx_stage_parcel_order", AcquisitionStage.parcel_id, AcquisitionStage.stage_order)
