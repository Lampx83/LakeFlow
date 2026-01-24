# src/eduai/catalog/db.py
import sqlite3
from pathlib import Path


def get_connection(db_path: Path) -> sqlite3.Connection:
    # Đảm bảo thư mục cha tồn tại
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        db_path,
        timeout=30,              # chờ lock lâu hơn
        isolation_level=None     # autocommit mode
    )

    # ⚠️ KHÔNG WAL trên NAS
    conn.execute("PRAGMA journal_mode=DELETE;")
    conn.execute("PRAGMA synchronous=FULL;")

    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_objects (
            hash TEXT PRIMARY KEY,
            domain TEXT,
            path TEXT,
            size INTEGER,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ingest_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT,
            hash TEXT,
            status TEXT,
            message TEXT,
            created_at TEXT
        )
    """)
