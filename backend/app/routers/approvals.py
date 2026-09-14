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
    """Return the full approval queue with counts and status breakdown.
    Counts are scoped to the current user's geographic jurisdiction.
    """
    from sqlalchemy import select, func, or_, and_
    from app.models import Document, ApprovalStatus, Parcel, Project
    from app.core.deps import get_user_geographic_scope
    from app.models.document_approval import BYPASS_ROLES

    queue_data = get_pending_approvals_for_user(db, current_user, page, page_size, status_filter=status)

    # Add summary counts across all statuses — scoped to user's geography
    scope = get_user_geographic_scope(current_user)
    counts = {}
    for status_val in ApprovalStatus:
        count_stmt = select(func.count(Document.document_id)).where(
            Document.approval_status == status_val.value
        )

        if scope and current_user.role not in BYPASS_ROLES:
            count_stmt = count_stmt.outerjoin(Project, Document.project_id == Project.project_id)
            count_stmt = count_stmt.outerjoin(Parcel, Document.parcel_id == Parcel.parcel_id)

            scope_clauses = []
            if scope.get("district"):
                scope_clauses.append(and_(Document.parcel_id.isnot(None), Parcel.district == scope["district"]))
                scope_clauses.append(and_(Document.project_id.isnot(None), Project.districts.any(scope["district"])))
            elif scope.get("state"):
                scope_clauses.append(and_(Document.parcel_id.isnot(None), Parcel.state == scope["state"]))
                scope_clauses.append(and_(Document.project_id.isnot(None), Project.states.any(scope["state"])))

            if scope_clauses:
                count_stmt = count_stmt.where(or_(*scope_clauses))
            else:
                count_stmt = count_stmt.where(Document.document_id.is_(None))

        count = db.execute(count_stmt).scalar() or 0
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
