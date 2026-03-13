from pathlib import Path
from typing import List, Tuple


def list_dir(path: Path) -> Tuple[List[Path], List[Path]]:
    dirs, files = [], []

    for p in sorted(path.iterdir()):
        if p.name.startswith("."):
            continue

        if p.is_dir():
            dirs.append(p)
        elif p.is_file():
            files.append(p)

    return dirs, files


def list_dir_safe(path: Path) -> Tuple[List[Path], List[Tuple[Path, int]]]:
    """
    Like list_dir but returns (dirs, [(file_path, size)]).
    Used for cache since size needed for display, avoids re-calling stat().
    """
    dirs, files = [], []
    for p in sorted(path.iterdir()):
        if p.name.startswith("."):
            continue
        if p.is_dir():
            dirs.append(p)
        elif p.is_file():
            try:
                files.append((p, p.stat().st_size))
            except OSError:
                files.append((p, 0))
    return dirs, files
