import os
from pathlib import Path
from dotenv import load_dotenv


def _load_env_from_project_root() -> None:
    """
    Tìm file .env bằng cách đi ngược lên cây thư mục
    Bắt đầu từ vị trí file hiện tại.
    """
    current = Path(__file__).resolve()

    for parent in [current] + list(current.parents):
        env_file = parent / ".env"
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
            return

    # Không raise ở đây – để fail-fast ở get_env()
    # Điều này giúp debug rõ ràng hơn


# Load .env ngay khi import module
_load_env_from_project_root()


def get_env(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def get_path(key: str) -> Path:
    return Path(get_env(key)).expanduser().resolve()
