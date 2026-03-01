import os
from pathlib import Path
from dotenv import load_dotenv


def _load_env_from_project_root() -> None:
    """
    Find .env file by walking up the directory tree
    starting from current file location.
    """
    current = Path(__file__).resolve()

    for parent in [current] + list(current.parents):
        env_file = parent / ".env"
        if env_file.exists():
            # override=True: .env overrides existing env vars (avoid /data from Docker when running dev)
            load_dotenv(dotenv_path=env_file, override=True)
            return

    # Do not raise here – let fail-fast happen in get_env()
    # This makes debugging clearer


# Load .env on module import
_load_env_from_project_root()


def get_env(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def get_path(key: str) -> Path:
    return Path(get_env(key)).expanduser().resolve()
