"""app.core — security utilities: JWT creation/verification and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

import bcrypt

def hash_password(plain: str) -> str:
    """Hash a plaintext password using standard bcrypt."""
    pwd_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


# Alias
get_password_hash = hash_password


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        pwd_bytes = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────
def create_access_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expiry_minutes
    )
    payload["exp"] = expire
    return jwt.encode(
        payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Raises JWTError if the token is invalid or expired."""
    return jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
