"""SQLAlchemy ORM model for Document (uploaded files)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, JSON
from app.models.types import PlatformUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import DocumentType


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        PlatformUUID, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=True, index=True
    )
    parcel_id: Mapped[uuid.UUID | None] = mapped_column(
        PlatformUUID, ForeignKey("parcels.parcel_id", ondelete="CASCADE"), nullable=True, index=True
    )
    stage_id: Mapped[uuid.UUID | None] = mapped_column(
        PlatformUUID, ForeignKey("acquisition_stages.stage_id", ondelete="SET NULL"), nullable=True, index=True
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        PlatformUUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/octet-stream")
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PlatformUUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
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
    project = relationship("Project", backref="documents")
    parcel = relationship("Parcel", backref="documents")
    stage = relationship("AcquisitionStage", backref="documents")


Index("idx_document_project_type", Document.project_id, Document.document_type)
Index("idx_document_parcel_type", Document.parcel_id, Document.document_type)
Index("idx_document_uploaded_by", Document.uploaded_by)