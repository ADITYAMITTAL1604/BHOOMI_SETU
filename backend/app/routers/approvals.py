"""FastAPI router for /approvals — multi-level document approval workflow endpoints."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.services.approval_service import (
    approve_document,
    get_approval_history,
    get_pending_approvals_for_user,
    reject_document,
    request_revision,
)

router = APIRouter()


class ApprovalActionRequest(BaseModel):
    remarks: Optional[str] = Field(None, max_length=2000)


class RejectReviseRequest(BaseModel):
    remarks: str = Field(..., min_length=5, max_length=2000)


@router.get(
    "/pending",
    summary="Get documents pending your approval",
    response_model=dict,
)
def list_pending_approvals(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return documents awaiting approval at the current user's approval chain step."""
    return get_pending_approvals_for_user(db, current_user, page, page_size, status_filter=status)


@router.get(
    "/queue",
    summary="Approval queue dashboard",
    response_model=dict,
)
def approval_queue_dashboard(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return the full approval queue with counts and status breakdown."""
    from sqlalchemy import select, func
    from app.models import Document, ApprovalStatus

    queue_data = get_pending_approvals_for_user(db, current_user, page, page_size, status_filter=status)

    # Add summary counts across all statuses
    counts = {}
    for status_val in ApprovalStatus:
        count = db.execute(
            select(func.count(Document.document_id)).where(
                Document.approval_status == status_val.value
            )
        ).scalar() or 0
        counts[status_val.value] = count

    queue_data["status_counts"] = counts
    return queue_data


@router.post(
    "/{document_id}/approve",
    summary="Approve a document at current approval step",
    response_model=dict,
)
def approve(
    document_id: UUID,
    body: ApprovalActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Approve the document — advances it to the next step in the approval chain."""
    ip = request.client.host if request.client else None
    return approve_document(db, document_id, current_user, body.remarks, ip)


@router.post(
    "/{document_id}/reject",
    summary="Reject a document (remarks required)",
    response_model=dict,
)
def reject(
    document_id: UUID,
    body: RejectReviseRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Reject the document — stops the approval chain entirely."""
    ip = request.client.host if request.client else None
    return reject_document(db, document_id, current_user, body.remarks, ip)


@router.post(
    "/{document_id}/revise",
    summary="Request revision (remarks required)",
    response_model=dict,
)
def revise(
    document_id: UUID,
    body: RejectReviseRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Request revision — sends document back to submitter for correction."""
    ip = request.client.host if request.client else None
    return request_revision(db, document_id, current_user, body.remarks, ip)


@router.get(
    "/{document_id}/history",
    summary="Get approval chain history for a document",
    response_model=list,
)
def history(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    """Return the full approval timeline for a document."""
    return get_approval_history(db, document_id)
