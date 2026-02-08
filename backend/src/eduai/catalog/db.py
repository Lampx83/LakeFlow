# src/eduai/catalog/db.py
import logging
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)


def _ensure_db_ready(db_path: Path) -> None:
    """Đảm bảo thư mục tồn tại; xóa file rỗng hoặc khi path là thư mục (sai) để tạo DB mới."""
    db_path = Path(db_path)
    parent = db_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    log.debug("Catalog DB parent dir: %s", parent)

    if not db_path.exists():
        log.debug("Catalog DB does not exist yet: %s", db_path)
        return

    if db_path.is_dir():
        log.warning("Catalog DB path is a directory (invalid), removing: %s", db_path)
        db_path.rmdir()
        return

    try:
        if db_path.stat().st_size == 0:
            log.warning("Catalog DB file is empty (0 bytes), removing: %s", db_path)
            db_path.unlink()
    except OSError as err:
        log.warning("Could not stat/unlink catalog DB %s: %s", db_path, err)


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path = Path(db_path).resolve()
    log.info("Catalog DB path: %s", db_path)
    _ensure_db_ready(db_path)

    def _connect() -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(db_path),
            timeout=30,
            isolation_level=None,
        )
        conn.execute("PRAGMA journal_mode=DELETE;")
        conn.execute("PRAGMA synchronous=FULL;")
        return conn

    try:
        return _connect()
    except sqlite3.DatabaseError as e:
        err_msg = str(e).lower()
        if "malformed" not in err_msg:
            log.exception("Catalog DB error (not malformed)")
            raise
        log.warning(
            "Catalog DB malformed, will remove and recreate: path=%s error=%s",
            db_path,
            e,
        )
        if db_path.exists():
            try:
                db_path.unlink()
                log.info("Removed malformed catalog DB; creating new one: %s", db_path)
            except OSError as err:
                log.error(
                    "Cannot remove malformed DB at %s (remove it manually): %s",
                    db_path,
                    err,
                )
                raise sqlite3.DatabaseError(
                    f"Cannot remove malformed DB at {db_path}; remove it manually."
                ) from e
        conn = _connect()
        log.info("Recreated catalog DB successfully: %s", db_path)
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
