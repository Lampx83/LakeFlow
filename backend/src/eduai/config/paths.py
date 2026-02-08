from pathlib import Path
from eduai.runtime.config import runtime_config


# =====================================================
# Helpers
# =====================================================

def _base() -> Path:
    """
    Lấy DATA_BASE_PATH tại runtime.
    """
    return runtime_config.get_data_base_path()


# =====================================================
# DATA LAKE ZONES (LAZY)
# =====================================================

def inbox_path() -> Path:
    return _base() / "000_inbox"


def raw_path() -> Path:
    return _base() / "100_raw"


def staging_path() -> Path:
    return _base() / "200_staging"


def processed_path() -> Path:
    return _base() / "300_processed"


def embeddings_path() -> Path:
    return _base() / "400_embeddings"


def catalog_path() -> Path:
    return _base() / "500_catalog"


# =====================================================
# CATALOG DB
# =====================================================

def catalog_db_path() -> Path:
    return catalog_path() / "catalog.sqlite"
