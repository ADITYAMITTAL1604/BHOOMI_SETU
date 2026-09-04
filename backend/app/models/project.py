"""SQLAlchemy ORM model for Project with PostGIS corridor geometry."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional
from geoalchemy2 import Geometry
from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ProjectStatus


from app.models.types import ArrayOrJSON, PlatformGeometry, PlatformUUID


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # Highway, Railway, Metro, Port, Industrial
    states: Mapped[list[str]] = mapped_column(ArrayOrJSON(String(100)), nullable=False, default=list)
    districts: Mapped[list[str]] = mapped_column(ArrayOrJSON(String(100)), nullable=False, default=list)
    land_required_ha: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    land_acquired_ha: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ProjectStatus.PLANNING.value, index=True
    )
    corridor_geometry = mapped_column(
        PlatformGeometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
        nullable=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PlatformUUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
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
    parcels = relationship(
        "Parcel", back_populates="project", cascade="all, delete-orphan"
    )
    history_snapshots = relationship(
        "ProjectHistory", back_populates="project", cascade="all, delete-orphan"
    )


Index("idx_project_status_type", Project.status, Project.type)
