"""app.core — FastAPI dependencies for authentication and authorization."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models import User
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode the bearer token and return the current user."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    stmt = select(User).where(User.id == UUID(user_id))
    user = db.execute(stmt).scalar_one_or_none()
    if user is None:
        raise credentials_exc
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (alias for get_current_user)."""
    return current_user


# Role-based access control
ROLE_HIERARCHY = {
    UserRole.ADMIN: 7,
    UserRole.CENTRAL: 6,
    UserRole.STATE: 5,
    UserRole.DISTRICT: 4,
    UserRole.PROJECT_AGENCY: 3,
    UserRole.FIELD_OFFICER: 2,
}


def require_role(*allowed_roles: UserRole):
    """Dependency that requires one of the allowed roles."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_level = ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = max(ROLE_HIERARCHY.get(role, 0) for role in allowed_roles)
        if user_role_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role.value} not authorized. Required: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require ADMIN role."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_central_or_above(current_user: User = Depends(get_current_user)) -> User:
    """Require CENTRAL or ADMIN role."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val not in (UserRole.CENTRAL.value, UserRole.ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Central or admin access required",
        )
    return current_user


def require_state_or_above(current_user: User = Depends(get_current_user)) -> User:
    """Require STATE, CENTRAL, or ADMIN role."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val not in (UserRole.STATE.value, UserRole.CENTRAL.value, UserRole.ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="State level or above access required",
        )
    return current_user


def require_district_or_above(current_user: User = Depends(get_current_user)) -> User:
    """Require DISTRICT, STATE, CENTRAL, or ADMIN role."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val not in (UserRole.DISTRICT.value, UserRole.STATE.value, UserRole.CENTRAL.value, UserRole.ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="District level or above access required",
        )
    return current_user


# Geographic scope filtering
def get_user_geographic_scope(user: User) -> dict:
    """Get the geographic scope for a user."""
    scope = {}
    if user.state_scope:
        scope["state"] = user.state_scope
    if user.district_scope:
        scope["district"] = user.district_scope
    return scope


def apply_geographic_scope(query, user: User, state_field: str = "state", district_field: str = "district"):
    """Apply geographic scope filter to a query based on user's assigned scope."""
    scope = get_user_geographic_scope(user)
    if scope.get("state"):
        query = query.where(getattr(query.column_descriptions[0]['type'], state_field) == scope["state"])
    if scope.get("district"):
        query = query.where(getattr(query.column_descriptions[0]['type'], district_field) == scope["district"])
    return query


def filter_by_geographic_scope(user: User, model, state_field: str = "state", district_field: str = "district"):
    """Return filter conditions for geographic scope."""
    conditions = []
    scope = get_user_geographic_scope(user)
    if scope.get("state"):
        conditions.append(getattr(model, state_field) == scope["state"])
    if scope.get("district"):
        conditions.append(getattr(model, district_field) == scope["district"])
    return conditions


# Permission decorators
def permission_required(resource: str, action: str):
    """
    Decorator to check if user has permission for a specific resource/action.
    Usage: @permission_required("projects", "read")
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # The current_user will be injected by FastAPI
            # This is a placeholder for more complex permission logic
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience dependencies for common role checks
admin_required = Depends(require_admin)
central_required = Depends(require_central_or_above)
state_required = Depends(require_state_or_above)
district_required = Depends(require_district_or_above)