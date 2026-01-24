from pathlib import Path
from typing import Optional


def find_raw_file(file_hash: str, raw_root: Path) -> Optional[Path]:
    """
    Tìm file raw theo hash trong 100_raw.

    Cấu trúc:
        100_raw/<domain>/<file_hash>.<ext>

    Trả về Path nếu tìm thấy, None nếu không.
    """

    for domain_dir in raw_root.iterdir():
        if not domain_dir.is_dir():
            continue

        for path in domain_dir.iterdir():
            if not path.is_file():
                continue

            if path.stem == file_hash:
                return path

    return None
