"""SQLAlchemy ORM model for Revenue & Registration (RR) Record."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from app.models.types import PlatformGeometry, PlatformUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AffectedType, RehabilitationStatus


class RRRecord(Base):
    __tablename__ = "rr_records"

    rr_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, ForeignKey("parcels.parcel_id", ondelete="CASCADE"), nullable=False, index=True
    )
    paf_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    paf_type: Mapped[str] = mapped_column(String(50), nullable=False, default=AffectedType.TITLE_HOLDER.value)
    family_size: Mapped[int] = mapped_column(nullable=False, default=1)
    affected_area_ha: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0.0)
    rehabilitation_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=RehabilitationStatus.IDENTIFIED.value, index=True
    )
    compensation_paid: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    relocation_site: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    plot_allotted: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    geometry = mapped_column(
        PlatformGeometry(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    parcel = relationship("Parcel", back_populates="rr_records")


Index("idx_rr_parcel_status", RRRecord.parcel_id, RRRecord.rehabilitation_status)
Index("idx_rr_paf_name", RRRecord.paf_name)