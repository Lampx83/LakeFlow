"""
Inbox Scanner

- Quét 000_inbox (toàn bộ hoặc chỉ các thư mục chỉ định)
- Chỉ yield FILE (không yield thư mục)
- Domain = thư mục cấp 1 dưới 000_inbox
- Có log tổng số file để debug / quan sát pipeline
"""

from pathlib import Path
from typing import Iterator, Optional

from eduai.pipelines.ingesting.models import InboxFile


# Các đuôi file được phép ingest
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".xls",
    ".pptx",
    ".txt",
}


def scan_inbox(
    inbox_root: Path,
    only_under: Optional[list[str]] = None,
) -> Iterator[InboxFile]:
    """
    Scan inbox_root (000_inbox) và yield InboxFile.

    only_under: nếu có, chỉ quét dưới các path này (vd: ["Regulations and Policies"]).
    Cấu trúc mong đợi:
        000_inbox/
            <domain>/
                <any_depth>/
                    file.ext

    Domain luôn là thư mục cấp 1 dưới inbox_root.
    """

    if not inbox_root.exists():
        print(f"[INBOX][ERROR] Inbox root does not exist: {inbox_root}")
        return

    if not inbox_root.is_dir():
        print(f"[INBOX][ERROR] Inbox root is not a directory: {inbox_root}")
        return

    # --------------------------------------------------
    # Chỉ quét dưới only_under nếu có; ngược lại quét toàn bộ
    # --------------------------------------------------
    if only_under:
        prefixes = [p.strip().rstrip("/") for p in only_under if p.strip()]
        file_paths = []
        for prefix in prefixes:
            sub_root = inbox_root / prefix
            if sub_root.exists() and sub_root.is_dir():
                file_paths.extend([p for p in sub_root.rglob("*") if p.is_file()])
        if prefixes and not file_paths:
            print(f"[INBOX] No files under selected folder(s): {prefixes}")
            return
    else:
        all_paths = list(inbox_root.rglob("*"))
        file_paths = [p for p in all_paths if p.is_file()]

    print(
        f"[INBOX] Scan complete: "
        f"{len(file_paths)} files found"
        + (f" under {only_under}" if only_under else f" under {inbox_root}")
    )

    if not file_paths:
        print("[INBOX][WARN] No files found in inbox")
        return

    # --------------------------------------------------
    # Yield files
    # --------------------------------------------------
    for path in file_paths:
        # ---------- Skip temp / system files ----------
        name = path.name

        if name.startswith("~$"):          # Office temp
            continue
        if name.startswith("."):           # .DS_Store, ._*
            continue
        if path.suffix.lower() in {".tmp", ".part"}:
            continue

        # ---------- Extension filter ----------
        ext = path.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            print(f"[INBOX][SKIP] Unsupported file type: {path}")
            continue

        # ---------- Determine domain ----------
        try:
            relative = path.relative_to(inbox_root)
        except ValueError:
            print(f"[INBOX][SKIP] Path outside inbox root: {path}")
            continue

        parts = relative.parts
        if len(parts) < 2:
            # file nằm trực tiếp dưới 000_inbox (không có domain)
            domain = "unknown"
            print(
                f"[INBOX][WARN] File without domain folder: {path}"
            )
        else:
            domain = parts[0]

        print(f"[INBOX][FILE] Domain={domain} Path={path}")

        yield InboxFile(
            path=path,
            domain=domain,
        )
