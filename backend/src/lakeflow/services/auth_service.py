# backend/src/lakeflow/services/auth_service.py

from datetime import timedelta

import logging

from lakeflow.core.security import verify_password, create_access_token, get_password_hash
from lakeflow.core.config import JWT_EXPIRE_MINUTES, ADMIN_USERNAME, ADMIN_PASSWORD_HASH, ADMIN_PASSWORD

log = logging.getLogger(__name__)

# =====================================================
# ADMIN USER (credentials come from .env only)
# =====================================================

FAKE_USER = {
    "username": ADMIN_USERNAME,
    "password_hash": ADMIN_PASSWORD_HASH or (get_password_hash(ADMIN_PASSWORD) if ADMIN_PASSWORD else None),
}

if not FAKE_USER["password_hash"]:
    log.warning("Neither LAKEFLOW_ADMIN_PASSWORD_HASH nor LAKEFLOW_ADMIN_PASSWORD is set: admin login is disabled.")


# =====================================================
# AUTHENTICATION
# =====================================================

def authenticate(username: str, password: str) -> str | None:
    if not FAKE_USER["password_hash"] or username != FAKE_USER["username"]:
        return None

    if not verify_password(password, FAKE_USER["password_hash"]):
        return None

    token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=JWT_EXPIRE_MINUTES),
    )

    return token
