# backend/src/lakeflow/services/auth_service.py

from datetime import timedelta

from lakeflow.core.security import verify_password, create_access_token
import logging

from lakeflow.core.config import JWT_EXPIRE_MINUTES, ADMIN_USERNAME, ADMIN_PASSWORD_HASH

log = logging.getLogger(__name__)

# =====================================================
# DEMO USER (DEV ONLY)
# =====================================================

FAKE_USER = {
    "username": ADMIN_USERNAME,
    # password = "admin123"
    "password_hash": ADMIN_PASSWORD_HASH or (
        "$2b$12$fu7BtRVkagxnaD22X5XfaO/"
        "VRKZiCOD7cPlQJOj93W3j7mTAoq6K."
    ),
}

if not ADMIN_PASSWORD_HASH:
    log.warning("LAKEFLOW_ADMIN_PASSWORD_HASH is not set: the demo admin password is active. "
                "Generate a bcrypt hash and set it in .env before exposing this service.")


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
