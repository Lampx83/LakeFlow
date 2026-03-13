from pathlib import Path
from lakeflow.runtime.config import runtime_config


def _base() -> Path:
    """
    Get DATA_BASE_PATH at runtime.
    """
    return runtime_config.get_data_base_path()


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


def catalog_db_path() -> Path:
    return catalog_path() / "catalog.sqlite"
