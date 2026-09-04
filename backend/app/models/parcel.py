"""SQLAlchemy ORM model for Parcel with PostGIS polygon geometry."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ParcelStatus, StageName


from app.models.types import PlatformGeometry, PlatformUUID


class Parcel(Base):
    __tablename__ = "parcels"

    parcel_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True
    )
    survey_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    area_ha: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    geometry = mapped_column(
        PlatformGeometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
        nullable=True,
    )
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    owner_reference: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    current_stage: Mapped[str] = mapped_column(
        String(50), nullable=False, default=StageName.PROPOSAL.value, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ParcelStatus.NOT_STARTED.value, index=True
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    village: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    assigned_officer: Mapped[Optional[uuid.UUID]] = mapped_column(
        PlatformUUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
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
    project = relationship("Project", back_populates="parcels")
    stages = relationship(
        "AcquisitionStage", back_populates="parcel", cascade="all, delete-orphan", order_by="AcquisitionStage.stage_order"
    )
    compensation = relationship(
        "Compensation", back_populates="parcel", uselist=False, cascade="all, delete-orphan"
    )
    rr_records = relationship(
        "RRRecord", back_populates="parcel", cascade="all, delete-orphan"
    )


# Performance & query indexes per TRD §3.2
Index("idx_parcel_state_district", Parcel.state, Parcel.district)
Index("idx_parcel_project_stage", Parcel.project_id, Parcel.current_stage)
Index("idx_parcel_risk_score", Parcel.risk_score.desc())
