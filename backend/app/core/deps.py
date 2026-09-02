"""app.core — FastAPI dependency that extracts and validates the current user from the JWT."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """Decode the bearer token and return the user_id claim."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exc
        return int(user_id)
    except (JWTError, ValueError):
        raise credentials_exc
