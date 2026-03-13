from pathlib import Path
from typing import Optional


def find_processed_dir(processed_root: Path, file_hash: str) -> Optional[Path]:
    """
    Find processed directory by file_hash in 300_processed.

    Structure:
        300_processed/<file_hash>/  (legacy, flat)
        300_processed/<domain>/<file_hash>/  (new)

    Returns Path to directory containing chunks.json if found, None otherwise.
    """

    flat_dir = processed_root / file_hash
    if flat_dir.is_dir() and (flat_dir / "chunks.json").exists():
        return flat_dir

    for entry in processed_root.iterdir():
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        sub_dir = entry / file_hash
        if sub_dir.is_dir() and (sub_dir / "chunks.json").exists():
            return sub_dir

    return None
