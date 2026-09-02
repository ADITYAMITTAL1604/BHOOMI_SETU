"""FastAPI router for authentication endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.database import get_db
from app.models import RefreshToken, User
from app.models.enums import UserRole

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: UserRole
    state_scope: str | None
    district_scope: str | None
    is_active: bool
    created_at: datetime


def create_refresh_token(db: Session, user_id: UUID) -> str:
    """Create and store a new refresh token."""
    import uuid
    token = str(uuid.uuid4())
    from datetime import timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()
    return token


def revoke_refresh_token(db: Session, token: str) -> None:
    """Revoke a refresh token."""
    stmt = select(RefreshToken).where(RefreshToken.token == token)
    refresh_token = db.execute(stmt).scalar_one_or_none()
    if refresh_token:
        refresh_token.is_revoked = True
        db.commit()


def verify_refresh_token(db: Session, token: str) -> RefreshToken | None:
    """Verify a refresh token is valid and not revoked."""
    stmt = select(RefreshToken).where(
        RefreshToken.token == token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    )
    return db.execute(stmt).scalar_one_or_none()


@router.post("/login", response_model=TokenResponse, summary="User login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return access + refresh tokens."""
    stmt = select(User).where(User.username == form_data.username)
    user = db.execute(stmt).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "state_scope": user.state_scope,
            "district_scope": user.district_scope,
        }
    )
    refresh_token = create_refresh_token(db, user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Refresh access token using refresh token."""
    refresh_token_obj = verify_refresh_token(db, request.refresh_token)
    if not refresh_token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Get user
    stmt = select(User).where(User.id == refresh_token_obj.user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Revoke old refresh token and create new one (rotation)
    revoke_refresh_token(db, request.refresh_token)
    new_refresh_token = create_refresh_token(db, user.id)

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "state_scope": user.state_scope,
            "district_scope": user.district_scope,
        }
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout", summary="User logout")
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Revoke refresh token (logout)."""
    revoke_refresh_token(db, request.refresh_token)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse, summary="Get current user info")
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)