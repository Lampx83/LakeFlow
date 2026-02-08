from pathlib import Path
import os


def get_token_root() -> Path:
    """
    Quy ước rõ ràng:
    - LAKEFLOW_RUNTIME=docker|prod  → /data
    - mặc định (local dev)          → ~/.lakeflow
    """

    runtime = os.getenv("LAKEFLOW_RUNTIME", "local").lower()

    if runtime in {"docker", "prod"}:
        return Path("/data")

    # Local dev (PyCharm, CLI, etc.)
    return Path.home() / ".lakeflow"


TOKEN_ROOT = get_token_root()
TOKEN_FILE = TOKEN_ROOT / ".lakeflow_token"


def save_token(token: str) -> None:
    TOKEN_ROOT.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token, encoding="utf-8")


def load_token() -> str | None:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    return None


def clear_token() -> None:
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
