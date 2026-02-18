from pathlib import Path
from typing import Optional


def find_processed_dir(processed_root: Path, file_hash: str) -> Optional[Path]:
    """
    Tìm thư mục processed theo file_hash trong 300_processed.

    Cấu trúc:
        300_processed/<file_hash>/  (cũ, phẳng)
        300_processed/<domain>/<file_hash>/  (mới)

    Trả về Path đến thư mục chứa chunks.json nếu tìm thấy, None nếu không.
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
