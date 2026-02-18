from pathlib import Path
from typing import List, Tuple


def list_dir(path: Path) -> Tuple[List[Path], List[Path]]:
    """
    Liệt kê thư mục con và file trong một thư mục.

    Parameters
    ----------
    path : Path
        Thư mục cần duyệt

    Returns
    -------
    (dirs, files) : tuple[list[Path], list[Path]]
        - dirs  : danh sách thư mục (đã sort theo tên)
        - files : danh sách file (đã sort theo tên)
    """

    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    dirs: List[Path] = []
    files: List[Path] = []

    for p in path.iterdir():
        # Skip hidden files / folders
        if p.name.startswith("."):
            continue

        if p.is_dir():
            dirs.append(p)
        elif p.is_file():
            files.append(p)

    # Sort for stable UI rendering
    dirs.sort(key=lambda x: x.name.lower())
    files.sort(key=lambda x: x.name.lower())

    return dirs, files
