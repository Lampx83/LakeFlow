from pathlib import Path
from typing import Iterator
from eduai.ingestion.models import InboxFile


def scan_inbox(inbox_root: Path) -> Iterator[InboxFile]:
    for path in inbox_root.rglob("*"):
        if not path.is_file():
            continue

        # Skip file tạm của cloud sync
        if path.name.startswith("~$"):
            continue
        if path.suffix.lower() in {".tmp", ".part"}:
            continue

        parts = path.relative_to(inbox_root).parts
        domain = parts[0] if len(parts) > 1 else "unknown"

        yield InboxFile(path=path, domain=domain)
