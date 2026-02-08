from pathlib import Path
from threading import RLock


class RuntimeConfig:
    """
    Runtime-safe configuration.
    Có thể thay đổi khi app đang chạy.
    """

    def __init__(self):
        self._lock = RLock()
        self._data_base_path: Path | None = None

    # -------------------------
    # Data Base Path
    # -------------------------
    def set_data_base_path(self, path: Path) -> None:
        with self._lock:
            self._data_base_path = Path(path)

    def get_data_base_path(self) -> Path:
        with self._lock:
            if self._data_base_path is None:
                raise RuntimeError(
                    "DATA_BASE_PATH is not configured at runtime"
                )
            return self._data_base_path


# Singleton (rất quan trọng)
runtime_config = RuntimeConfig()
