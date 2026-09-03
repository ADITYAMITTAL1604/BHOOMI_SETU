"""SQLAlchemy ORM model for Compensation."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from app.models.types import PlatformUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import CompensationPaymentStatus


class Compensation(Base):
    __tablename__ = "compensation"

    compensation_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, ForeignKey("parcels.parcel_id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    assessed_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.00)
    approved_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.00)
    paid_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.00)
    payment_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=CompensationPaymentStatus.PENDING.value, index=True
    )
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    parcel = relationship("Parcel", back_populates="compensation")
