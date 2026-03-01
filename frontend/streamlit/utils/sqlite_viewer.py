import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import List

import pandas as pd


def copy_db_to_temp(db_path: Path, max_retries: int = 3) -> Path:
    """
    Copy SQLite DB to temp local — avoids Errno 35 (resource deadlock) when reading from
    shared NAS/Docker volume (backend and frontend both access).
    """
    db_path = Path(db_path).resolve()
    try:
        local_temp_dir = Path(tempfile.gettempdir())
    except Exception:
        local_temp_dir = Path(".").resolve()
    fd, temp_path = tempfile.mkstemp(suffix=".sqlite", dir=local_temp_dir)
    os.close(fd)
    temp_path = Path(temp_path)
    last_err = None
    for attempt in range(max_retries):
        try:
            shutil.copy2(db_path, temp_path)
            if temp_path.stat().st_size != db_path.stat().st_size:
                raise OSError("Copy size mismatch")
            break
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))
    else:
        temp_path.unlink(missing_ok=True)
        raise last_err
    return temp_path


def connect_readonly(db_path: Path, timeout: float = 15.0) -> sqlite3.Connection:
    path_str = str(Path(db_path).resolve().as_posix())
    return sqlite3.connect(
        f"file:{path_str}?mode=ro",
        uri=True,
        timeout=timeout,
        check_same_thread=False,
    )


def list_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    return [row[0] for row in cur.fetchall()]


def get_table_schema(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    return pd.read_sql(
        f"PRAGMA table_info({table})",
        conn,
    )


def preview_table(
    conn: sqlite3.Connection,
    table: str,
    limit: int = 100,
) -> pd.DataFrame:
    return pd.read_sql(
        f"SELECT * FROM {table} LIMIT {limit}",
        conn,
    )
