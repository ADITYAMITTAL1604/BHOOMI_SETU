"""FastAPI router for /audit-log — searchable, filterable, append-only audit log (admin-only)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.database import get_db
from app.models import AuditLog, User

router = APIRouter()


@router.get(
    "",
    summary="Search and filter the immutable audit log (admin only)",
    response_model=dict,
)
def list_audit_log(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (e.g. parcel, project)"),
    entity_id: Optional[UUID] = Query(None, description="Filter by specific entity UUID"),
    action: Optional[str] = Query(None, description="Filter by action keyword (e.g. STAGE_TRANSITION)"),
    user_id: Optional[UUID] = Query(None, description="Filter by actor user UUID"),
    date_from: Optional[datetime] = Query(None, description="ISO datetime lower bound (inclusive)"),
    date_to: Optional[datetime] = Query(None, description="ISO datetime upper bound (inclusive)"),
    before_id: Optional[UUID] = Query(None, description="Cursor: return entries before this log_id's timestamp"),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Return filtered, paginated audit log entries.

    This is a read-only, append-only view. No entries can be modified or deleted
    via this endpoint. Entries are ordered by created_at descending (most recent first).
    """
    stmt = select(AuditLog)
    conditions = []

    if entity_type:
        conditions.append(AuditLog.entity_type == entity_type)
    if entity_id:
        conditions.append(AuditLog.entity_id == entity_id)
    if action:
        conditions.append(AuditLog.action.ilike(f"%{action}%"))
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if date_from:
        conditions.append(AuditLog.created_at >= date_from)
    if date_to:
        conditions.append(AuditLog.created_at <= date_to)

    # Cursor-style pagination: entries before a given log_id timestamp
    if before_id:
        before_log = db.execute(
            select(AuditLog.created_at).where(AuditLog.log_id == before_id)
        ).scalar_one_or_none()
        if before_log:
            conditions.append(AuditLog.created_at < before_log)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(total_stmt).scalar() or 0

    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(page_size)
    entries = db.execute(stmt).scalars().all()

    next_cursor = str(entries[-1].log_id) if entries else None

    return {
        "entries": [
            {
                "log_id": str(e.log_id),
                "user_id": str(e.user_id) if e.user_id else None,
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": str(e.entity_id),
                "old_values": e.old_values,
                "new_values": e.new_values,
                "ip_address": e.ip_address,
                "user_agent": e.user_agent,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
        "total_matched": total,
        "returned": len(entries),
        "next_cursor": next_cursor,
        "filters_applied": {
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "action": action,
            "user_id": str(user_id) if user_id else None,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
        },
    }
