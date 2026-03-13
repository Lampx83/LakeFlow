# src/lakeflow/common/hashing.py
import hashlib
import time
from pathlib import Path
from typing import Iterable

# Reduce buffer to avoid timeout on NAS
BUFFER_SIZE = 1 * 1024 * 1024  # 1MB

MAX_RETRIES = 5
RETRY_DELAY = 1.0  # seconds

# Common transient I/O errors on macOS + CloudStorage
RETRY_ERRNOS = {
    60,  # Operation timed out
    89,  # Operation canceled
}


class TemporaryIOError(RuntimeError):
    """Transient I/O error (NAS / Cloud sync)."""


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

            # Serious I/O error → raise immediately
            raise

    # Exhausted retries → treat as transient error
    raise TemporaryIOError(
        f"Temporary I/O error after {MAX_RETRIES} retries: {path}"
    ) from last_error
