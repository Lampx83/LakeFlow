from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from eduai.core.config import JWT_SECRET_KEY, JWT_ALGORITHM


# =====================================================
# OAuth2 scheme
# =====================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# =====================================================
# Verify JWT token
# =====================================================

def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Verify JWT access token.

    - Trả về payload nếu hợp lệ
    - Raise HTTP 401 nếu token không hợp lệ / hết hạn
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
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Kiểm tra payload tối thiểu
    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload không hợp lệ",
        )

    return payload
