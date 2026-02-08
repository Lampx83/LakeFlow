# backend/src/eduai/services/auth_service.py

from datetime import timedelta

from eduai.core.security import verify_password, create_access_token
from eduai.core.config import JWT_EXPIRE_MINUTES

# =====================================================
# DEMO USER (DEV ONLY)
# =====================================================

FAKE_USER = {
    "username": "admin",
    # password = "admin123"
    "password_hash": (
        "$2b$12$fu7BtRVkagxnaD22X5XfaO/"
        "VRKZiCOD7cPlQJOj93W3j7mTAoq6K."
    ),
}


# =====================================================
# AUTHENTICATION
# =====================================================

def authenticate(username: str, password: str) -> str | None:
    if username != FAKE_USER["username"]:
        return None

    if not verify_password(password, FAKE_USER["password_hash"]):
        return None

    token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=JWT_EXPIRE_MINUTES),
    )

    return token
