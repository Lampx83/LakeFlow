"""
NAS/NFS-safe I/O: retry when reading/writing to mount (avoid Errno 35 Resource deadlock avoided).
Used for 300_processed, 400_embeddings when running on Synology/NFS (including in Docker).
"""

import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

from lakeflow.common.jsonio import read_json

NAS_RETRIES = 8
NAS_RETRY_DELAY = 1.5


def nas_safe_exists(path: Path) -> bool:
    """Path.exists() with retry — avoid Errno 35 on NAS/shared volume."""
    for attempt in range(NAS_RETRIES):
        try:
            return path.exists()
        except OSError:
            if attempt == NAS_RETRIES - 1:
                raise
            time.sleep(NAS_RETRY_DELAY * (attempt + 1))
    return False  # unreachable


def nas_safe_is_dir(path: Path) -> bool:
    """Path.is_dir() with retry — avoid Errno 35 on NAS/shared volume."""
    for attempt in range(NAS_RETRIES):
        try:
            return path.is_dir()
        except OSError:
            if attempt == NAS_RETRIES - 1:
                raise
            time.sleep(NAS_RETRY_DELAY * (attempt + 1))
    return False  # unreachable


def nas_safe_listdir(path: Path) -> list[Path]:
    """path.iterdir() to list with retry — avoid Errno 35 on NAS/shared volume."""
    for attempt in range(NAS_RETRIES):
        try:
            return list(path.iterdir())
        except OSError:
            if attempt == NAS_RETRIES - 1:
                raise
            time.sleep(NAS_RETRY_DELAY * (attempt + 1))
    return []  # unreachable


def nas_safe_read_json(path: Path) -> Any:
    for attempt in range(NAS_RETRIES):
        try:
            return read_json(path)
        except OSError:
            if attempt == NAS_RETRIES - 1:
                raise
            time.sleep(NAS_RETRY_DELAY * (attempt + 1))
    raise RuntimeError("Unreachable")


def nas_safe_load_npy(path: Path):
    import numpy as np
    for attempt in range(NAS_RETRIES):
        try:
            return np.load(path)
        except OSError:
            if attempt == NAS_RETRIES - 1:
                raise
            time.sleep(NAS_RETRY_DELAY * (attempt + 1))
    raise RuntimeError("Unreachable")


def nas_safe_mkdir(path: Path) -> None:
    for attempt in range(NAS_RETRIES):
        try:
            path.mkdir(parents=True, exist_ok=True)
            return
        except OSError:
            if attempt == NAS_RETRIES - 1:
                raise
            time.sleep(NAS_RETRY_DELAY * (attempt + 1))


def nas_safe_copy(src: Path, dst: Path) -> None:
    for attempt in range(NAS_RETRIES):
        try:
            shutil.copy2(src, dst)
            return
        except OSError:
            if attempt == NAS_RETRIES - 1:
                raise
            time.sleep(NAS_RETRY_DELAY * (attempt + 1))


def nas_safe_find_processed_dir(processed_root: Path, file_hash: str, parent_dir: Optional[str] = None) -> Optional[Path]:
    """
    Find processed_dir for file_hash. If parent_dir provided, do not iterdir on NAS.
    Retries when calling .exists() / .is_dir().
    """
    candidates: list[Path] = []
    if parent_dir:
        candidates.append(processed_root / parent_dir / file_hash)
        candidates.append(processed_root / file_hash)
    else:
        candidates.append(processed_root / file_hash)
        for attempt in range(NAS_RETRIES):
            try:
                for entry in processed_root.iterdir():
                    if not entry.is_dir() or entry.name.startswith("."):
                        continue
                    candidates.append(entry / file_hash)
                break
            except OSError:
                if attempt == NAS_RETRIES - 1:
                    raise
                time.sleep(NAS_RETRY_DELAY * (attempt + 1))
    for d in candidates:
        for attempt in range(NAS_RETRIES):
            try:
                if d.is_dir() and (d / "chunks.json").exists():
                    return d
                break
            except OSError:
                if attempt == NAS_RETRIES - 1:
                    raise
                time.sleep(NAS_RETRY_DELAY * (attempt + 1))
    return None
