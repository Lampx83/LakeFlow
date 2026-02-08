# src/eduai/ingesting/models.py
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InboxFile:
    path: Path
    domain: str
