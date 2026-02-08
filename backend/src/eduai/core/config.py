import os
from pathlib import Path

# =====================================================
# ENVIRONMENT
# =====================================================

ENV = os.getenv("ENV", "development")
DEBUG = ENV == "development"

# =====================================================
# BASE PATH
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_BASE_PATH = os.getenv(
    "DATA_BASE_PATH",
    str(BASE_DIR / "data"),
)

# =====================================================
# JWT / AUTH
# =====================================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "DEV_ONLY_CHANGE_ME_IMMEDIATELY",
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)

# =====================================================
# QDRANT
# =====================================================

QDRANT_HOST = os.getenv(
    "QDRANT_HOST",
    "localhost",
)

QDRANT_PORT = int(
    os.getenv("QDRANT_PORT", "6333")
)

QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY",
    None
)

QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"


def get_qdrant_url(override: str | None = None) -> str:
    """URL Qdrant dùng cho request: override nếu có, không thì dùng env (mặc định dev=localhost:6333, docker=eduai-qdrant:6333 qua QDRANT_HOST)."""
    if override and (s := override.strip()):
        return s if s.startswith("http://") or s.startswith("https://") else f"http://{s}"
    return QDRANT_URL

# =====================================================
# OPENAI / LLM
# =====================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)  # For custom endpoints

# =====================================================
# LOG BOOT INFO (DEV ONLY)
# =====================================================

if DEBUG:
    print("[BOOT] ENV =", ENV)
    print("[BOOT] DEBUG =", DEBUG)
    print("[BOOT] DATA_BASE_PATH1 =", DATA_BASE_PATH)
    print("[BOOT] JWT_ALGORITHM =", JWT_ALGORITHM)
    print("[BOOT] JWT_EXPIRE_MINUTES =", JWT_EXPIRE_MINUTES)
    print("[BOOT] QDRANT_URL =", QDRANT_URL)
