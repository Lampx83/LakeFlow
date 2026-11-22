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


# --- Cho phép gọi /ask từ mạng nội bộ (AI Portal gọi agent không kèm token) ---
# Bản vá 18/11 bắt /ask phải có token → Portal (không gửi token) bị 401, trợ lý ngừng chạy.
# Giữ bảo vệ từ Internet: IP công khai vẫn phải có Bearer token hợp lệ.
import ipaddress as _ip
from fastapi import Request as _Request

_INTERNAL_NETS = [_ip.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8")]


def verify_token_or_internal(request: _Request) -> dict:
    host = request.client.host if request.client else ""
    try:
        if any(_ip.ip_address(host) in n for n in _INTERNAL_NETS):
            return {"sub": "internal", "ip": host}
    except ValueError:
        pass
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=i18n_detail("auth.token_invalid_or_expired"),
                            headers={"WWW-Authenticate": "Bearer"})
    return verify_token(auth.split(" ", 1)[1].strip())
