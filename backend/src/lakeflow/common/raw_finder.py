from pathlib import Path
from typing import Optional


def find_raw_file(file_hash: str, raw_root: Path, parent_dir: Optional[str] = None) -> Optional[Path]:
    """
    Find raw file by hash in 100_raw.

    Structure:
        100_raw/<parent_dir>/<file_hash>.<ext>  (parent_dir can be nested, e.g. "Library/Quy định hướng dẫn")

    If parent_dir is given, look only in raw_root / parent_dir.
    Otherwise search recursively under raw_root.
    Returns Path if found, None otherwise.
    """
    if parent_dir:
        search_dir = raw_root / parent_dir
        if not search_dir.is_dir():
            return None
        for path in search_dir.iterdir():
            if path.is_file() and path.stem == file_hash:
                return path
        return None

    for path in raw_root.rglob("*"):
        if path.is_file() and path.stem == file_hash:
            return path
    return None
