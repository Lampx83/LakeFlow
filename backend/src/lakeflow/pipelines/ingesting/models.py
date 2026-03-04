# src/lakeflow/ingesting/models.py
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InboxFile:
    path: Path
    domain: str
    """Path of the file's parent directory relative to inbox root (e.g. 'Library' or 'Library/Quy định hướng dẫn')."""
    relative_dir: str
