# src/eduai/ingestion/pipeline.py
from pathlib import Path
import sqlite3

from eduai.ingestion.inbox_scanner import scan_inbox
from eduai.ingestion.raw_ingestor import RawIngestor


def run_ingestion(
    inbox_root: Path,
    raw_root: Path,
    conn: sqlite3.Connection
) -> None:
    ingestor = RawIngestor(raw_root, conn)

    for inbox_file in scan_inbox(inbox_root):
        ingestor.ingest(inbox_file)
