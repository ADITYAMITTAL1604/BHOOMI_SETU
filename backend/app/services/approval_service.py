"""BhoomiSetu Approval Service — multi-level document approval chain engine."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import (
    AuditLog, Document, User,
    ApprovalAction, ApprovalStatus,
)
from app.models.document_approval import (
    DocumentApproval, APPROVAL_CHAIN, BYPASS_ROLES,
)

logger = logging.getLogger(__name__)


def get_approval_step_for_role(role: str) -> Optional[dict]:
    """Return the approval chain step config for a given role, or None."""
    for step_cfg in APPROVAL_CHAIN:
        if step_cfg["role"] == role:
            return step_cfg
    return None


def get_next_step(current_step: int) -> Optional[dict]:
    """Return the next approval chain step config, or None if chain is complete."""
    for step_cfg in APPROVAL_CHAIN:
        if step_cfg["step"] == current_step + 1:
            return step_cfg
    return None


def get_pending_approvals_for_user(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Return documents awaiting approval at the current user's chain step."""
    role = user.role

    # Bypass roles see all pending documents
    if role in BYPASS_ROLES:
        stmt = select(Document).where(
            Document.approval_status.in_([
                ApprovalStatus.PENDING_REVIEW.value,
                ApprovalStatus.UNDER_REVIEW.value,
            ])
        )
    else:
        step_cfg = get_approval_step_for_role(role)
        if not step_cfg:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

        step_order = step_cfg["step"]
        stmt = select(Document).where(
            Document.current_approval_step == step_order - 1,
            Document.approval_status.in_([
                ApprovalStatus.PENDING_REVIEW.value,
                ApprovalStatus.UNDER_REVIEW.value,
            ])
        )

    # Geographic scope filtering
    from app.core.deps import get_user_geographic_scope, filter_by_geographic_scope
    from app.models import Parcel, Project

    scope = get_user_geographic_scope(user)
    if scope:
        parcel_conditions = filter_by_geographic_scope(user, Parcel)
        if parcel_conditions:
            stmt = stmt.outerjoin(Parcel, Document.parcel_id == Parcel.parcel_id)
            stmt = stmt.where(*parcel_conditions)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    stmt = stmt.order_by(Document.created_at.desc())
    offset = (page - 1) * page_size
    docs = db.execute(stmt.offset(offset).limit(page_size)).scalars().all()

    return {
        "items": [_document_to_dict(d) for d in docs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def approve_document(
    db: Session,
    document_id: uuid.UUID,
    approver: User,
    remarks: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict:
    """Approve a document at the current user's approval step."""
    doc = _get_document_or_404(db, document_id)
    _validate_can_act(doc, approver)

    step_order = _resolve_step_order(doc, approver)

    # Create approval record
    approval = DocumentApproval(
        approval_id=uuid.uuid4(),
        document_id=document_id,
        approver_id=approver.id,
        approver_role=approver.role,
        action=ApprovalAction.APPROVED.value,
        step_order=step_order,
        remarks=remarks,
    )
    db.add(approval)

    # Advance to next step or complete
    doc.current_approval_step = step_order
    next_step = get_next_step(step_order)

    if next_step is None or approver.role in BYPASS_ROLES:
        # Chain complete — document fully approved
        doc.approval_status = ApprovalStatus.APPROVED.value
        doc.is_verified = True
        doc.verified_by = approver.id
        doc.verified_at = datetime.now(timezone.utc)
    else:
        doc.approval_status = ApprovalStatus.UNDER_REVIEW.value

    # Audit log
    _write_approval_audit(
        db, approver, doc,
        action="DOCUMENT_APPROVED",
        old_step=step_order - 1,
        new_step=step_order,
        remarks=remarks,
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(doc)

    # Notification for next approver or submitter
    _send_approval_notification(db, doc, approver, ApprovalAction.APPROVED, remarks)

    return _document_to_dict(doc)


def reject_document(
    db: Session,
    document_id: uuid.UUID,
    approver: User,
    remarks: str,
    ip_address: Optional[str] = None,
) -> dict:
    """Reject a document — stops the approval chain."""
    if not remarks or not remarks.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Remarks are mandatory when rejecting a document.",
        )

    doc = _get_document_or_404(db, document_id)
    _validate_can_act(doc, approver)

    step_order = _resolve_step_order(doc, approver)

    approval = DocumentApproval(
        approval_id=uuid.uuid4(),
        document_id=document_id,
        approver_id=approver.id,
        approver_role=approver.role,
        action=ApprovalAction.REJECTED.value,
        step_order=step_order,
        remarks=remarks,
    )
    db.add(approval)

    doc.approval_status = ApprovalStatus.REJECTED.value

    _write_approval_audit(
        db, approver, doc,
        action="DOCUMENT_REJECTED",
        old_step=step_order - 1,
        new_step=step_order,
        remarks=remarks,
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(doc)

    _send_approval_notification(db, doc, approver, ApprovalAction.REJECTED, remarks)

    return _document_to_dict(doc)


def request_revision(
    db: Session,
    document_id: uuid.UUID,
    approver: User,
    remarks: str,
    ip_address: Optional[str] = None,
) -> dict:
    """Request revision — sends document back to submitter."""
    if not remarks or not remarks.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Remarks are mandatory when requesting revision.",
        )

    doc = _get_document_or_404(db, document_id)
    _validate_can_act(doc, approver)

    step_order = _resolve_step_order(doc, approver)

    approval = DocumentApproval(
        approval_id=uuid.uuid4(),
        document_id=document_id,
        approver_id=approver.id,
        approver_role=approver.role,
        action=ApprovalAction.REVISION_REQUESTED.value,
        step_order=step_order,
        remarks=remarks,
    )
    db.add(approval)

    doc.approval_status = ApprovalStatus.REVISION_REQUESTED.value
    doc.current_approval_step = 0  # Reset chain

    _write_approval_audit(
        db, approver, doc,
        action="DOCUMENT_REVISION_REQUESTED",
        old_step=step_order - 1,
        new_step=0,
        remarks=remarks,
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(doc)

    _send_approval_notification(db, doc, approver, ApprovalAction.REVISION_REQUESTED, remarks)

    return _document_to_dict(doc)


def get_approval_history(db: Session, document_id: uuid.UUID) -> list[dict]:
    """Return the full approval chain history for a document."""
    approvals = db.execute(
        select(DocumentApproval)
        .where(DocumentApproval.document_id == document_id)
        .order_by(DocumentApproval.created_at.asc())
    ).scalars().all()

    result = []
    for a in approvals:
        approver = db.execute(
            select(User).where(User.id == a.approver_id)
        ).scalar_one_or_none()

        result.append({
            "approval_id": str(a.approval_id),
            "document_id": str(a.document_id),
            "approver_id": str(a.approver_id) if a.approver_id else None,
            "approver_username": approver.username if approver else None,
            "approver_role": a.approver_role,
            "action": a.action,
            "step_order": a.step_order,
            "step_label": _get_step_label(a.step_order),
            "remarks": a.remarks,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return result


# ── Private helpers ──────────────────────────────────────────────────────────


def _get_document_or_404(db: Session, document_id: uuid.UUID) -> Document:
    doc = db.execute(
        select(Document).where(Document.document_id == document_id)
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


def _validate_can_act(doc: Document, approver: User) -> None:
    """Validate the approver can act on this document at its current step."""
    if doc.approval_status in (
        ApprovalStatus.APPROVED.value,
        ApprovalStatus.REJECTED.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document is already {doc.approval_status}. No further actions allowed.",
        )

    if approver.role in BYPASS_ROLES:
        return  # Admin/Central can always act

    step_cfg = get_approval_step_for_role(approver.role)
    if not step_cfg:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{approver.role}' is not part of the approval chain.",
        )

    expected_step = doc.current_approval_step + 1
    if step_cfg["step"] != expected_step:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Document is at approval step {doc.current_approval_step}. "
                f"Expected role for step {expected_step}, but your role maps to step {step_cfg['step']}."
            ),
        )


def _resolve_step_order(doc: Document, approver: User) -> int:
    """Determine the step order for this approval action."""
    if approver.role in BYPASS_ROLES:
        return len(APPROVAL_CHAIN)  # Final step
    step_cfg = get_approval_step_for_role(approver.role)
    return step_cfg["step"] if step_cfg else doc.current_approval_step + 1


def _get_step_label(step_order: int) -> str:
    for step_cfg in APPROVAL_CHAIN:
        if step_cfg["step"] == step_order:
            return step_cfg["label"]
    return f"Step {step_order}"


def _document_to_dict(doc: Document) -> dict:
    return {
        "document_id": str(doc.document_id),
        "title": doc.title,
        "document_type": doc.document_type,
        "approval_status": doc.approval_status,
        "current_approval_step": doc.current_approval_step,
        "total_approval_steps": len(APPROVAL_CHAIN),
        "mime_type": doc.mime_type,
        "file_size_bytes": doc.file_size_bytes,
        "is_verified": doc.is_verified,
        "project_id": str(doc.project_id) if doc.project_id else None,
        "parcel_id": str(doc.parcel_id) if doc.parcel_id else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }


def _write_approval_audit(
    db: Session,
    approver: User,
    doc: Document,
    action: str,
    old_step: int,
    new_step: int,
    remarks: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    audit = AuditLog(
        log_id=uuid.uuid4(),
        user_id=approver.id,
        action=action,
        entity_type="document",
        entity_id=doc.document_id,
        old_values={
            "approval_status": doc.approval_status,
            "approval_step": old_step,
        },
        new_values={
            "approval_status": doc.approval_status,
            "approval_step": new_step,
            "approver_role": approver.role,
            "remarks": remarks,
        },
        ip_address=ip_address,
    )
    db.add(audit)


def _send_approval_notification(
    db: Session,
    doc: Document,
    actor: User,
    action: ApprovalAction,
    remarks: Optional[str],
) -> None:
    """Create notifications for relevant parties after an approval action."""
    try:
        from app.services.notification_service import create_notification

        if action == ApprovalAction.APPROVED:
            if doc.approval_status == ApprovalStatus.APPROVED.value:
                # Fully approved — notify submitter
                if doc.uploaded_by:
                    create_notification(
                        db,
                        user_id=doc.uploaded_by,
                        title=f"Document Approved: {doc.title}",
                        message=f"Your document '{doc.title}' has been fully approved through all levels.",
                        severity="INFO",
                        category="approval",
                        entity_type="document",
                        entity_id=doc.document_id,
                        action_url=f"/documents",
                    )
            else:
                # Partial approval — notify next approver
                next_step = get_next_step(doc.current_approval_step)
                if next_step:
                    _notify_role_users(
                        db, doc, next_step["role"],
                        title=f"Approval Pending: {doc.title}",
                        message=f"Document '{doc.title}' requires your approval (Step {next_step['step']}: {next_step['label']}).",
                        category="approval",
                    )

        elif action in (ApprovalAction.REJECTED, ApprovalAction.REVISION_REQUESTED):
            # Notify submitter
            action_label = "rejected" if action == ApprovalAction.REJECTED else "sent back for revision"
            if doc.uploaded_by:
                create_notification(
                    db,
                    user_id=doc.uploaded_by,
                    title=f"Document {action_label.title()}: {doc.title}",
                    message=f"Your document '{doc.title}' was {action_label} by {actor.username}. Remarks: {remarks or 'None'}",
                    severity="WARNING",
                    category="approval",
                    entity_type="document",
                    entity_id=doc.document_id,
                    action_url=f"/documents",
                )

        db.commit()
    except Exception:
        logger.exception("Failed to send approval notification for document %s", doc.document_id)


def _notify_role_users(
    db: Session,
    doc: Document,
    role: str,
    title: str,
    message: str,
    category: str = "approval",
) -> None:
    """Send notification to all active users of a given role within geographic scope."""
    from app.services.notification_service import create_notification
    from app.models import Parcel

    # Determine geographic scope from the document's parcel
    state, district = None, None
    if doc.parcel_id:
        parcel = db.execute(
            select(Parcel).where(Parcel.parcel_id == doc.parcel_id)
        ).scalar_one_or_none()
        if parcel:
            state = parcel.state
            district = parcel.district

    users = db.execute(
        select(User).where(User.role == role, User.is_active == True)  # noqa: E712
    ).scalars().all()

    for user in users:
        # Geographic scope check
        if user.district_scope and district and user.district_scope != district:
            continue
        if user.state_scope and state and user.state_scope != state:
            continue

        create_notification(
            db,
            user_id=user.id,
            title=title,
            message=message,
            severity="INFO",
            category=category,
            entity_type="document",
            entity_id=doc.document_id,
            action_url=f"/approvals",
        )
