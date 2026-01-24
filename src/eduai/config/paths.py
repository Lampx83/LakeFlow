# src/eduai/config/paths.py
from pathlib import Path
from eduai.config.env import get_path

# =========================
# BASE PATH (from .env)
# =========================
DATA_BASE_PATH: Path = get_path("EDUAI_DATA_BASE_PATH")

# =========================
# DATA LAKE ZONES
# =========================
INBOX_PATH: Path = DATA_BASE_PATH / "000_inbox"
RAW_PATH: Path = DATA_BASE_PATH / "100_raw"
STAGING_PATH: Path = DATA_BASE_PATH / "200_staging"
PROCESSED_PATH: Path = DATA_BASE_PATH / "300_processed"
EMBEDDINGS_PATH: Path = DATA_BASE_PATH / "400_embeddings"
CATALOG_PATH: Path = DATA_BASE_PATH / "500_catalog"

# =========================
# CATALOG DB
# =========================
CATALOG_DB_PATH: Path = CATALOG_PATH / "catalog.sqlite"
