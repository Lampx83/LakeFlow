"""
System APIs – Runtime Configuration

- Manage Data Lake path
- Config overview (safe, no secrets)
- Zones status and create
- Runtime-safe
- Sync for FastAPI + subprocess pipelines
"""

from pathlib import Path
import os

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from lakeflow.i18n import i18n_detail, SUPPORTED_LOCALES, DEFAULT_LOCALE

from lakeflow.runtime.config import runtime_config
from lakeflow.core.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    LLM_BASE_URL,
    LLM_MODEL,
    OPENAI_API_KEY,
)
from lakeflow.services.ollama_embed_service import EMBED_MODEL

router = APIRouter(
    prefix="/system",
    tags=["system"],
)


@router.get("/locales")
def get_locales():
    """
    List supported locales for i18n.
    Returns: locales[], default.
    Client can use ?locale= or Accept-Language to get translated API messages.
    """
    return {
        "locales": SUPPORTED_LOCALES,
        "default": DEFAULT_LOCALE,
    }


class DataPathRequest(BaseModel):
    path: str


class DataPathResponse(BaseModel):
    data_base_path: str | None


REQUIRED_ZONES = [
    "000_inbox",
    "100_raw",
    "200_staging",
    "300_processed",
    "400_embeddings",
    "500_catalog",
]


def validate_data_lake_root(path: Path) -> None:
    """
    Validate Data Lake root directory structure.
    Raises HTTPException if invalid.
    """
    if not path.exists():
        raise HTTPException(
            status_code=400,
            detail=i18n_detail("system.data_lake_not_exist"),
        )

    if not path.is_dir():
        raise HTTPException(
            status_code=400,
            detail=i18n_detail("system.data_lake_not_dir"),
        )

    missing = [z for z in REQUIRED_ZONES if not (path / z).exists()]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=i18n_detail("system.missing_zones", missing=missing),
        )


@router.get(
    "/data-path",
    response_model=DataPathResponse,
)
def get_data_path():
    """
    Get current Data Lake path (runtime).

    Returns:
    - path (str) if set
    - null if not configured
    """
    try:
        path = runtime_config.get_data_base_path()
        return DataPathResponse(
            data_base_path=str(path)
        )
    except RuntimeError:
        return DataPathResponse(
            data_base_path=None
        )


@router.post("/data-path")
def set_data_path(req: DataPathRequest):
    """
    Set Data Lake path for entire system.

    Takes effect:
    - Immediately for FastAPI runtime
    - Immediately for Pipeline subprocess
    """

    path = Path(req.path).expanduser().resolve()
    validate_data_lake_root(path)

    runtime_config.set_data_base_path(path)
    os.environ["LAKE_ROOT"] = str(path)

    return {
        "status": "ok",
        "data_base_path": str(path),
    }


@router.get("/health-detail")
def get_health_detail():
    """
    Health check for backend + Qdrant connectivity.
    """
    from lakeflow.core.config import get_qdrant_url

    qdrant_ok = False
    qdrant_error = None
    qdrant_url = get_qdrant_url()
    try:
        collections_url = f"{qdrant_url.rstrip('/')}/collections"
        r = requests.get(collections_url, timeout=5)
        qdrant_ok = r.status_code == 200
        if not qdrant_ok:
            qdrant_error = f"Qdrant returned {r.status_code}"
    except Exception as e:
        qdrant_error = str(e)

    return {
        "backend": "ok",
        "qdrant_connected": qdrant_ok,
        "qdrant_error": qdrant_error,
        "qdrant_url": qdrant_url,
    }


@router.get("/config")
def get_config():
    """
    Get safe runtime config (no secrets). For System Settings UI.
    """
    try:
        data_path = str(runtime_config.get_data_base_path())
    except RuntimeError:
        data_path = None

    llm_display = "(not set)" if not LLM_BASE_URL else f"{LLM_BASE_URL.rstrip('/')}/... (hidden)"
    openai_set = bool(OPENAI_API_KEY)

    return {
        "data_base_path": data_path,
        "qdrant_host": QDRANT_HOST,
        "qdrant_port": str(QDRANT_PORT),
        "qdrant_url": f"http://{QDRANT_HOST}:{QDRANT_PORT}",
        "embed_model": EMBED_MODEL,
        "llm_base_url_set": bool(LLM_BASE_URL),
        "llm_base_url_display": llm_display,
        "llm_model": LLM_MODEL,
        "openai_api_key_set": openai_set,
        "lakeflow_mode": os.getenv("LAKEFLOW_MODE", ""),
        "mount_description": os.getenv("LAKEFLOW_MOUNT_DESCRIPTION", "").strip(),
    }


def _count_files_in_zone(path: Path, extensions: set | None = None) -> int:
    """Count files in zone. extensions=None = count all files."""
    if not path.exists() or not path.is_dir():
        return 0
    n = 0
    for p in path.rglob("*"):
        if p.is_file():
            if extensions is None or p.suffix.lower() in extensions:
                n += 1
    return n


@router.get("/zones-status")
def get_zones_status():
    """
    Status of each Data Lake zone: exists, file count.
    """
    try:
        base = runtime_config.get_data_base_path()
    except RuntimeError:
        return {"zones": [], "data_base_path": None}

    zones = []
    zone_files = {
        "000_inbox": None,  # all files
        "100_raw": None,    # all (pdf, docx, etc.)
        "200_staging": {".json"},
        "300_processed": {".json"},
        "400_embeddings": {".npy"},
        "500_catalog": {".sqlite", ".db"},
    }
    for zone in REQUIRED_ZONES:
        p = base / zone
        exists = p.exists() and p.is_dir()
        count = _count_files_in_zone(p, zone_files.get(zone)) if exists else 0
        zones.append({
            "zone": zone,
            "path": str(p),
            "exists": exists,
            "file_count": count,
        })

    return {
        "data_base_path": str(base),
        "zones": zones,
        "all_zones_exist": all(z["exists"] for z in zones),
    }


@router.post("/create-zones")
def create_zones():
    """
    Create missing zone directories in current Data Lake path.
    Idempotent: skips zones that already exist.
    """
    try:
        base = runtime_config.get_data_base_path()
    except RuntimeError:
        raise HTTPException(
            status_code=400,
            detail=i18n_detail("system.data_path_not_configured"),
        )

    if not base.exists():
        raise HTTPException(
            status_code=400,
            detail=i18n_detail("system.data_root_not_exist"),
        )

    created = []
    for zone in REQUIRED_ZONES:
        p = base / zone
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(zone)

    return {
        "status": "ok",
        "data_base_path": str(base),
        "created": created,
        "message": f"Created {len(created)} zone(s)" if created else "All zones already exist",
    }
