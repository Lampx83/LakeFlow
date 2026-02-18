# src/lakeflow/catalog/db.py
import logging
import os
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)


def _ensure_db_ready(db_path: Path) -> None:
    """Đảm bảo thư mục tồn tại; xóa file rỗng hoặc khi path là thư mục (sai) để tạo DB mới."""
    db_path = Path(db_path).resolve()
    parent = db_path.parent
    parent_str = os.path.abspath(str(parent))
    os.makedirs(parent_str, exist_ok=True)
    log.debug("Catalog DB parent dir: %s", parent_str)

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
    db_path_str = os.path.abspath(str(db_path))
    log.info("Catalog DB path: %s", db_path_str)
    _ensure_db_ready(db_path)

    def _connect() -> sqlite3.Connection:
        os.makedirs(os.path.dirname(db_path_str), exist_ok=True)
        conn = sqlite3.connect(
            db_path_str,
            timeout=30,
            isolation_level=None,
        )
        conn.execute("PRAGMA journal_mode=DELETE;")
        conn.execute("PRAGMA synchronous=FULL;")
        return conn

    try:
        return _connect()
    except sqlite3.OperationalError as e:
        err_msg = str(e).lower()
        if "unable to open database file" not in err_msg:
            log.exception("Catalog DB error")
            raise
        dir_str = os.path.dirname(db_path_str)
        log.warning("Catalog DB cannot be opened (path=%s), ensuring directory and retrying: %s", db_path_str, e)
        os.makedirs(dir_str, mode=0o755, exist_ok=True)
        try:
            return _connect()
        except sqlite3.OperationalError as e2:
            fallback_dir = "/tmp/lakeflow_catalog"
            fallback_path = os.path.join(fallback_dir, "catalog.sqlite")
            log.warning(
                "Không ghi được DB tại %s (quyền thư mục). Dùng fallback: %s (dữ liệu mất khi container tắt)",
                db_path_str,
                fallback_path,
            )
            os.makedirs(fallback_dir, mode=0o755, exist_ok=True)
            try:
                conn = sqlite3.connect(
                    fallback_path,
                    timeout=30,
                    isolation_level=None,
                )
                conn.execute("PRAGMA journal_mode=DELETE;")
                conn.execute("PRAGMA synchronous=FULL;")
                return conn
            except sqlite3.OperationalError as e3:
                log.exception("Không mở được cả DB gốc và fallback.")
                raise sqlite3.OperationalError(
                    f"unable to open database file: {db_path_str}. Fallback {fallback_path} cũng lỗi: {e3}"
                ) from e3
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
