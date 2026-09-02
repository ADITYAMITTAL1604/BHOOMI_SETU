"""FastAPI router for admin-only management endpoints (TRD §4.11)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.core.security import get_password_hash
from app.database import get_db
from app.models import AuditLog, User
from app.models.enums import UserRole

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole
    state_scope: Optional[str] = None
    district_scope: Optional[str] = None


class UserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None
    state_scope: Optional[str] = None
    district_scope: Optional[str] = None
    is_active: Optional[bool] = None


class ResetPasswordRequest(BaseModel):
    new_password: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/users",
    summary="List users (admin-only)",
    response_model=dict,
)
def list_users(
    role: Optional[str] = Query(None),
    state_scope: Optional[str] = Query(None),
    district_scope: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> dict:
    """Return paginated user accounts with role and scope filters."""
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if state_scope:
        stmt = stmt.where(User.state_scope == state_scope)
    if district_scope:
        stmt = stmt.where(User.district_scope == district_scope)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    offset = (page - 1) * page_size
    users = db.execute(stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)).scalars().all()

    return {
        "items": [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "state_scope": u.state_scope,
                "district_scope": u.district_scope,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, -(-total // page_size)),
        },
    }


@router.post(
    "/users",
    summary="Create a new user (admin-only)",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def create_user(
    body: UserCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> dict:
    """Create a new user account with specified role and scope."""
    # Check duplicate username
    existing_user = db.execute(
        select(User).where(User.username == body.username)
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already registered.",
        )

    # Check duplicate email
    existing_email = db.execute(
        select(User).where(User.email == body.email)
    ).scalar_one_or_none()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{body.email}' is already registered.",
        )

    hashed = get_password_hash(body.password)
    user = User(
        username=body.username,
        email=body.email,
        password_hash=hashed,
        role=body.role.value,
        state_scope=body.state_scope,
        district_scope=body.district_scope,
        is_active=True,
    )
    db.add(user)
    db.flush()

    audit = AuditLog(
        user_id=admin_user.id,
        action="CREATE_USER",
        entity_type="user",
        entity_id=user.id,
        new_values={
            "username": user.username,
            "role": user.role,
            "state_scope": user.state_scope,
            "district_scope": user.district_scope,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "state_scope": user.state_scope,
        "district_scope": user.district_scope,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else datetime.now(timezone.utc).isoformat(),
    }


@router.put(
    "/users/{user_id}",
    summary="Update a user's role, scope, or active status (admin-only)",
    response_model=dict,
)
def update_user(
    user_id: UUID,
    body: UserUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> dict:
    """Update role, state/district scope, or activate/deactivate account."""
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_vals = {
        "role": user.role,
        "state_scope": user.state_scope,
        "district_scope": user.district_scope,
        "is_active": user.is_active,
    }

    if body.role is not None:
        user.role = body.role.value
    if body.state_scope is not None:
        user.state_scope = body.state_scope
    if body.district_scope is not None:
        user.district_scope = body.district_scope
    if body.is_active is not None:
        user.is_active = body.is_active

    audit = AuditLog(
        user_id=admin_user.id,
        action="UPDATE_USER",
        entity_type="user",
        entity_id=user.id,
        old_values=old_vals,
        new_values={
            "role": user.role,
            "state_scope": user.state_scope,
            "district_scope": user.district_scope,
            "is_active": user.is_active,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "state_scope": user.state_scope,
        "district_scope": user.district_scope,
        "is_active": user.is_active,
    }


@router.delete(
    "/users/{user_id}",
    summary="Deactivate a user (admin-only)",
    response_model=dict,
)
def deactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> dict:
    """Soft-deactivate a user account to preserve audit integrity."""
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate own admin account.",
        )

    user.is_active = False
    audit = AuditLog(
        user_id=admin_user.id,
        action="DEACTIVATE_USER",
        entity_type="user",
        entity_id=user.id,
        new_values={"is_active": False},
    )
    db.add(audit)
    db.commit()

    return {"message": f"User '{user.username}' deactivated successfully.", "is_active": False}


@router.post(
    "/users/{user_id}/reset-password",
    summary="Reset a user's password (admin-only)",
    response_model=dict,
)
def reset_user_password(
    user_id: UUID,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> dict:
    """Reset password for any user account."""
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.password_hash = get_password_hash(body.new_password)
    audit = AuditLog(
        user_id=admin_user.id,
        action="RESET_PASSWORD",
        entity_type="user",
        entity_id=user.id,
        new_values={"reset_by": str(admin_user.id)},
    )
    db.add(audit)
    db.commit()

    return {"message": f"Password for user '{user.username}' has been reset successfully."}
