from fastapi import Depends, HTTPException, status

from lakeflow.i18n import i18n_detail
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from lakeflow.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ADMIN_USERNAME


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Verify JWT access token.

    - Returns payload if valid
    - Raises HTTP 401 if token invalid / expired
    """

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=i18n_detail("auth.token_invalid_or_expired"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check minimum payload
    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=i18n_detail("auth.token_payload_invalid"),
        )

    return payload


def require_admin(payload: dict = Depends(verify_token)) -> dict:
    """Dependency: valid token AND the admin account. Raises 403 otherwise."""
    if payload.get("sub") != ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=i18n_detail("admin.admin_only"),
        )
    return payload
