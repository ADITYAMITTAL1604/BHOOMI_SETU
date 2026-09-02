"""SQLAlchemy ORM model for GISBoundary — administrative boundary polygons."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


from app.models.types import PlatformGeometry, PlatformUUID


class GISBoundary(Base):
    """Administrative boundary (state / district / village) stored as PostGIS geometry."""

    __tablename__ = "gis_boundaries"

    boundary_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )
    level: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True  # 'state' | 'district' | 'village'
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    parent_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    state_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    district_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # MultiPolygon column
    geometry = mapped_column(
        PlatformGeometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


Index("idx_boundary_level_name", GISBoundary.level, GISBoundary.name)
Index("idx_boundary_state", GISBoundary.state_name)
Index("idx_boundary_district", GISBoundary.district_name)
