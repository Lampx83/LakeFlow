from neuai.backend.core.security import verify_password, create_access_token
from neuai.backend.core.config import ACCESS_TOKEN_EXPIRE_MINUTES

# DEMO: hardcode user (dev mode)
FAKE_USER = {
    "username": "admin",
    # password = "admin123"
    "password_hash": "$2b$12$fu7BtRVkagxnaD22X5XfaO/VRKZiCOD7cPlQJOj93W3j7mTAoq6K."
}


def authenticate(username: str, password: str):
    if username != FAKE_USER["username"]:
        return None

    if not verify_password(password, FAKE_USER["password_hash"]):
        return None

    token = create_access_token(
        data={"sub": username},
        expires_minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return token
