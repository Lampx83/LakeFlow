# src/eduai/ingesting/raw_ingestor.py
from pathlib import Path
from datetime import datetime
import sqlite3

from eduai.common.hashing import sha256_file, TemporaryIOError
from eduai.common.filesystem import atomic_copy
from eduai.pipelines.ingesting.models import InboxFile
from eduai.pipelines.ingesting.verifier import verify_hash
from eduai.pipelines.ingesting.deduplicator import hash_exists


class RawIngestor:

    def __init__(self, raw_root: Path, conn: sqlite3.Connection):
        self.raw_root = raw_root
        self.conn = conn

    def ingest(self, inbox_file: InboxFile, force: bool = False) -> None:
        src = inbox_file.path
        domain = inbox_file.domain

        print(f"[INGEST] Start: {src}")

        # ---------- HASH ----------
        try:
            print("[INGEST]   Hashing file...")
            file_hash = sha256_file(src)
            print(f"[INGEST]   Hash = {file_hash[:16]}...")
        except TemporaryIOError as exc:
            self._log(src, None, "TEMP_ERROR", str(exc))
            print(f"[INGEST][SKIP] Temporary I/O error, skip file")
            return

        ext = src.suffix
        raw_path = self.raw_root / domain / f"{file_hash}{ext}"
        now = datetime.utcnow().isoformat()

        # ---------- DEDUP (bỏ qua nếu force) ----------
        if not force and hash_exists(self.conn, file_hash):
            print("[INGEST]   Duplicate detected, skip copy")
            self._log(src, file_hash, "DUPLICATE", "Hash already exists")
            return

        # ---------- COPY ----------
        print(f"[INGEST]   Copy to raw: {raw_path}")
        atomic_copy(src, raw_path)

        # ---------- VERIFY ----------
        print("[INGEST]   Verifying hash...")
        if not verify_hash(raw_path, file_hash):
            self._log(src, file_hash, "ERROR", "Hash verification failed")
            print("[INGEST][ERROR] Hash verification failed")
            raise RuntimeError("Hash verification failed")

        # ---------- DB ----------
        if hash_exists(self.conn, file_hash):
            print("[INGEST]   Updating catalog (force re-ingest)")
            self.conn.execute(
                "UPDATE raw_objects SET path = ?, size = ?, created_at = ? WHERE hash = ?",
                (str(raw_path), src.stat().st_size, now, file_hash),
            )
        else:
            print("[INGEST]   Writing metadata to catalog")
            self.conn.execute(
                "INSERT INTO raw_objects VALUES (?, ?, ?, ?, ?)",
                (file_hash, domain, str(raw_path), src.stat().st_size, now),
            )
        self._log(src, file_hash, "COPIED", None)
        self.conn.commit()

        print("[INGEST] Completed successfully")

    def _log(
        self,
        src: Path,
        hash_value: str | None,
        status: str,
        message: str | None
    ):
        print(f"[DB]   Log status={status}")
        self.conn.execute(
            "INSERT INTO ingest_log VALUES (NULL, ?, ?, ?, ?, ?)",
            (str(src), hash_value, status, message, datetime.utcnow().isoformat())
        )
