from neuai.catalog.db import get_connection, init_db
from neuai.ingestion.pipeline import run_ingestion
from neuai.config.paths import INBOX_PATH, RAW_PATH, CATALOG_DB_PATH

conn = get_connection(CATALOG_DB_PATH)
init_db(conn)

run_ingestion(INBOX_PATH, RAW_PATH, conn)

print("Ingestion completed successfully.")
