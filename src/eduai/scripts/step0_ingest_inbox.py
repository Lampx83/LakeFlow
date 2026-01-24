from eduai.catalog.db import get_connection, init_db
from eduai.ingestion.pipeline import run_ingestion
from eduai.config.paths import INBOX_PATH, RAW_PATH, CATALOG_DB_PATH

conn = get_connection(CATALOG_DB_PATH)
init_db(conn)

run_ingestion(INBOX_PATH, RAW_PATH, conn)

print("Ingestion completed successfully.")
