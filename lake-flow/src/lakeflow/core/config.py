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

# =====================================================
# LLM (Q&A / RAG) – Ollama proxy (mặc định) hoặc OpenAI
# =====================================================
# Mặc định: Ollama qua Research (LLM_BASE_URL + LLM_MODEL), không cần API key.
# Để dùng OpenAI: set OPENAI_API_KEY (và tùy chọn OPENAI_BASE_URL, OPENAI_MODEL).

_llm_base = (os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL") or "").strip()
_openai_base = (os.getenv("OPENAI_BASE_URL") or "").strip()
LLM_BASE_URL = _llm_base or _openai_base or "https://research.neu.edu.vn/ollama"
LLM_MODEL = (os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "qwen3:8b").strip()
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()


def get_qdrant_url(override: str | None = None) -> str:
    """URL Qdrant dùng cho request: override nếu có, không thì dùng env (mặc định dev=localhost:6333, docker=lakeflow-qdrant:6333 qua QDRANT_HOST)."""
    if override and (s := override.strip()):
        return s if s.startswith("http://") or s.startswith("https://") else f"http://{s}"
    return QDRANT_URL

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
    print("[BOOT] LLM_BASE_URL =", LLM_BASE_URL, "LLM_MODEL =", LLM_MODEL, "OPENAI_API_KEY set =", bool(OPENAI_API_KEY))
