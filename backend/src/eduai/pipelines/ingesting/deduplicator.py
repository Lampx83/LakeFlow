# src/eduai/ingesting/deduplicator.py
import sqlite3


def hash_exists(conn: sqlite3.Connection, hash_value: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM raw_objects WHERE hash = ? LIMIT 1",
        (hash_value,)
    )
    return cur.fetchone() is not None
