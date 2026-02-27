# src/lakeflow/common/filesystem.py
import os
import shutil
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_copy(src: Path, dst: Path) -> None:
    src = Path(src)
    dst = Path(dst).resolve()
    parent_str = os.path.dirname(os.path.abspath(str(dst)))
    os.makedirs(parent_str, exist_ok=True)
    tmp_str = parent_str + os.sep + Path(dst).name + ".tmp"
    with open(str(src), "rb") as f_in:
        with open(tmp_str, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.replace(tmp_str, str(dst))
    try:
        shutil.copystat(str(src), str(dst))
    except OSError:
        pass
