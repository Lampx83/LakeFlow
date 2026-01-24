# src/eduai/common/hashing.py
import hashlib
import time
from pathlib import Path
from typing import Iterable

# Giảm buffer để tránh timeout trên NAS
BUFFER_SIZE = 1 * 1024 * 1024  # 1MB

MAX_RETRIES = 5
RETRY_DELAY = 1.0  # seconds

# Các lỗi I/O tạm thời thường gặp trên macOS + CloudStorage
RETRY_ERRNOS = {
    60,  # Operation timed out
    89,  # Operation canceled
}


class TemporaryIOError(RuntimeError):
    """Lỗi I/O tạm thời (NAS / Cloud sync)."""


def sha256_file(path: Path) -> str:
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            hasher = hashlib.sha256()
            with path.open("rb") as f:
                while True:
                    try:
                        chunk = f.read(BUFFER_SIZE)
                    except TimeoutError as exc:
                        raise exc

                    if not chunk:
                        break
                    hasher.update(chunk)

            return hasher.hexdigest()

        except (OSError, TimeoutError) as exc:
            last_error = exc

            errno = getattr(exc, "errno", None)
            if errno in RETRY_ERRNOS:
                time.sleep(RETRY_DELAY)
                continue

            # Lỗi I/O nghiêm trọng → raise ngay
            raise

    # Retry hết số lần vẫn fail → coi là lỗi tạm thời
    raise TemporaryIOError(
        f"Temporary I/O error after {MAX_RETRIES} retries: {path}"
    ) from last_error
