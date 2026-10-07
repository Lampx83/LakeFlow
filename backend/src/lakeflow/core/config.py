import json
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
# LLM (Q&A / RAG) – Ollama proxy (default) or OpenAI
# =====================================================
# Default: Ollama via Research (LLM_BASE_URL + LLM_MODEL), no API key needed.
# To use OpenAI: set OPENAI_API_KEY (and optionally OPENAI_BASE_URL, OPENAI_MODEL).

_llm_base = (os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL") or "").strip()
_openai_base = (os.getenv("OPENAI_BASE_URL") or "").strip()
LLM_BASE_URL = _llm_base or _openai_base
LLM_MODEL = (os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "qwen3:8b").strip()
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()


def _json_env(name: str) -> dict:
    """Parse a JSON-object env var; empty/invalid → {}."""
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


# Extra HTTP headers for the chat endpoint, e.g. {"x-ollama-seckey": "..."} (gateway auth).
LLM_EXTRA_HEADERS = _json_env("LLM_EXTRA_HEADERS")
# Extra JSON body fields merged into chat requests, e.g. {"chat_template_kwargs": {"enable_thinking": false}}.
LLM_EXTRA_BODY = _json_env("LLM_EXTRA_BODY")
# Extra HTTP headers for the embed endpoint (may use a different key than chat).
EMBED_EXTRA_HEADERS = _json_env("EMBED_EXTRA_HEADERS")


def llm_headers() -> dict:
    """Headers for chat requests: JSON, optional Bearer key, plus LLM_EXTRA_HEADERS."""
    headers = {"Content-Type": "application/json"}
    if OPENAI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    headers.update(LLM_EXTRA_HEADERS)
    return headers


def get_qdrant_url(override: str | None = None) -> str:
    """Qdrant URL for requests: use override if provided, else env (default dev=localhost:6333, docker=lakeflow-qdrant:6333 via QDRANT_HOST)."""
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
