import sqlite3
from pathlib import Path
import pandas as pd
from typing import List


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
