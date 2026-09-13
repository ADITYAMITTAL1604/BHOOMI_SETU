"""SQLAlchemy ORM model for DocumentApproval — multi-level approval chain."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from app.models.types import PlatformUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ApprovalAction


# Approval chain step order mapped to roles (configurable)
APPROVAL_CHAIN = [
    {"step": 1, "role": "FIELD_OFFICER", "label": "Tehsildar / Field Officer Review"},
    {"step": 2, "role": "DISTRICT", "label": "District Land Acquisition Officer"},
    {"step": 3, "role": "STATE", "label": "State Nodal Officer"},
    {"step": 4, "role": "PROJECT_AGENCY", "label": "Project Authority — Final Approval"},
]

# Roles that can bypass the approval chain entirely
BYPASS_ROLES = {"ADMIN", "CENTRAL"}


class DocumentApproval(Base):
    __tablename__ = "document_approvals"

    approval_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, ForeignKey("documents.document_id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    approver_id: Mapped[uuid.UUID] = mapped_column(
        PlatformUUID, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    approver_role: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ApprovalAction.APPROVED.value, index=True
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    document = relationship("Document", backref="approvals")
    approver = relationship("User", foreign_keys=[approver_id])


# Indexes for common query patterns
Index("idx_approval_doc_step", DocumentApproval.document_id, DocumentApproval.step_order)
Index("idx_approval_approver", DocumentApproval.approver_id, DocumentApproval.action)
Index("idx_approval_created", DocumentApproval.created_at.desc())
