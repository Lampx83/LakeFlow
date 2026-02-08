"""
System APIs – Runtime Configuration

- Quản lý Data Lake path
- Runtime-safe
- Đồng bộ cho FastAPI + subprocess pipelines
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import os

from eduai.runtime.config import runtime_config


# ======================================================
# Router
# ======================================================

router = APIRouter(
    prefix="/system",
    tags=["system"],
)


# ======================================================
# Schemas
# ======================================================

class DataPathRequest(BaseModel):
    path: str


class DataPathResponse(BaseModel):
    data_base_path: str | None


# ======================================================
# Internal helpers
# ======================================================

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
    Raise HTTPException nếu không hợp lệ.
    """
    if not path.exists():
        raise HTTPException(
            status_code=400,
            detail="Data Lake path does not exist"
        )

    if not path.is_dir():
        raise HTTPException(
            status_code=400,
            detail="Data Lake path is not a directory"
        )

    missing = [z for z in REQUIRED_ZONES if not (path / z).exists()]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required zones: {missing}"
        )


# ======================================================
# API
# ======================================================

@router.get(
    "/data-path",
    response_model=DataPathResponse,
)
def get_data_path():
    """
    Lấy Data Lake path hiện tại (runtime).

    Trả về:
    - path (str) nếu đã set
    - null nếu chưa được cấu hình
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
    Set Data Lake path cho toàn bộ hệ thống.

    Hiệu lực:
    - Ngay lập tức cho FastAPI runtime
    - Ngay lập tức cho Pipeline subprocess
    """

    # ---------- Resolve & validate ----------
    path = Path(req.path).expanduser().resolve()
    validate_data_lake_root(path)

    # ---------- 1. Set runtime (FastAPI process) ----------
    runtime_config.set_data_base_path(path)

    # ---------- 2. Sync ENV cho subprocess (CRITICAL) ----------
    os.environ["EDUAI_DATA_BASE_PATH"] = str(path)

    return {
        "status": "ok",
        "data_base_path": str(path),
    }
