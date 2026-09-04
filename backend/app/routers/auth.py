"""FastAPI router for authentication endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, EmailStr
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
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    role: UserRole
    state_scope: str | None
    district_scope: str | None
    is_active: bool
    created_at: datetime


from app.config import get_settings
from app.models.audit_log import AuditLog
from sqlalchemy import update
import uuid

settings = get_settings()


def create_refresh_token(db: Session, user_id: UUID) -> str:
    """Create and store a new refresh token with configured expiry."""
    token = str(uuid.uuid4())
    from datetime import timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expiry_days)

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


def revoke_all_user_refresh_tokens(db: Session, user_id: UUID) -> int:
    """Revoke ALL refresh tokens for a user (token family invalidation on breach)."""
    result = db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
        .values(is_revoked=True)
    )
    db.commit()
    return result.rowcount


def verify_refresh_token(db: Session, token: str) -> tuple[RefreshToken | None, bool]:
    """Verify a refresh token. Returns (token_obj, is_reuse_attack)."""
    stmt = select(RefreshToken).where(RefreshToken.token == token)
    refresh_token = db.execute(stmt).scalar_one_or_none()

    if not refresh_token:
        return None, False

    if refresh_token.is_revoked:
        # Token was previously revoked: potential token reuse attack!
        return refresh_token, True

    exp = refresh_token.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp <= datetime.now(timezone.utc):
        return None, False

    return refresh_token, False


@router.post("/login", response_model=TokenResponse, summary="User login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return access + refresh tokens."""
    stmt = select(User).where(User.username == form_data.username)
    user = db.execute(stmt).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        if user:
            db.add(
                AuditLog(
                    log_id=uuid.uuid4(),
                    user_id=user.id,
                    action="LOGIN_FAILED",
                    entity_type="user",
                    entity_id=user.id,
                    new_values={"username": form_data.username, "reason": "invalid_credentials"},
                    created_at=datetime.now(timezone.utc),
                )
            )
            db.commit()
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

    db.add(
        AuditLog(
            log_id=uuid.uuid4(),
            user_id=user.id,
            action="LOGIN_SUCCESS",
            entity_type="user",
            entity_id=user.id,
            new_values={"username": user.username, "role": user.role.value if hasattr(user.role, "value") else str(user.role)},
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Refresh access token using refresh token with reuse detection."""
    token_obj, is_reuse_attack = verify_refresh_token(db, request.refresh_token)

    if is_reuse_attack and token_obj:
        # Security incident: Invalidate all tokens for this user
        revoked_count = revoke_all_user_refresh_tokens(db, token_obj.user_id)
        db.add(
            AuditLog(
                log_id=uuid.uuid4(),
                user_id=token_obj.user_id,
                action="TOKEN_REUSE_DETECTED",
                entity_type="user",
                entity_id=token_obj.user_id,
                new_values={"compromised_token": request.refresh_token[:8] + "...", "revoked_sessions": revoked_count},
                created_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compromised token detected: refresh token was already revoked. All active sessions invalidated.",
        )

    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Get user
    stmt = select(User).where(User.id == token_obj.user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Revoke old refresh token and create new one (token rotation)
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

    db.add(
        AuditLog(
            log_id=uuid.uuid4(),
            user_id=user.id,
            action="TOKEN_REFRESH",
            entity_type="user",
            entity_id=user.id,
            new_values={"username": user.username},
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

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
    stmt = select(RefreshToken).where(RefreshToken.token == request.refresh_token)
    refresh_token_obj = db.execute(stmt).scalar_one_or_none()

    if refresh_token_obj:
        refresh_token_obj.is_revoked = True
        db.add(
            AuditLog(
                log_id=uuid.uuid4(),
                user_id=refresh_token_obj.user_id,
                action="LOGOUT",
                entity_type="user",
                entity_id=refresh_token_obj.user_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse, summary="Get current user info")
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)