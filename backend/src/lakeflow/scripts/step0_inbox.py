"""
Step 0 – Inbox Ingestion
000_inbox → 100_raw
"""

from pathlib import Path
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
)

from lakeflow.runtime.config import runtime_config
from lakeflow.catalog.db import get_connection, init_db
from lakeflow.pipelines.ingesting.pipeline import run_ingestion
from lakeflow.config import paths

from dotenv import load_dotenv
load_dotenv()

data_base = os.getenv("LAKE_ROOT")
if not data_base:
    raise RuntimeError(
        "LAKE_ROOT is not set. "
        "Example: export LAKE_ROOT=/path/to/data_lake"
    )

data_base_path = Path(data_base).expanduser().resolve()
runtime_config.set_data_base_path(data_base_path)

print(f"[BOOT] DATA_BASE_PATH = {data_base_path}")


conn = get_connection(paths.catalog_db_path())
init_db(conn)


print("=== RUN INGESTION (000_inbox → 100_raw) ===")

only_folders_env = os.getenv("PIPELINE_ONLY_FOLDERS")
only_path_prefixes = [s.strip() for s in (only_folders_env or "").split(",") if s.strip()] or None
force_rerun = os.getenv("PIPELINE_FORCE_RERUN") == "1"
if only_path_prefixes:
    print(f"[INBOX] Running only folders: {only_path_prefixes}")
if force_rerun:
    print("[INBOX] Force re-run: run again even if already ingested")

before = conn.execute(
    "SELECT COUNT(*) FROM raw_objects"
).fetchone()[0]

run_ingestion(
    inbox_root=paths.inbox_path(),
    raw_root=paths.raw_path(),
    conn=conn,
    only_path_prefixes=only_path_prefixes,
    force_rerun=force_rerun,
)

after = conn.execute(
    "SELECT COUNT(*) FROM raw_objects"
).fetchone()[0]

print("\n📦 INGESTION SUMMARY")
print(f"Files before : {before}")
print(f"Files after  : {after}")
print(f"New ingested : {after - before}")
