# backend/src/lakeflow/api/qdrant.py

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from lakeflow.core.auth import verify_token
from lakeflow.services.qdrant_service import (
    list_collections,
    get_collection_detail,
    list_points,
    filter_points,
)

router = APIRouter(
    prefix="/qdrant",
    tags=["Qdrant"],
)

class QdrantFilterRequest(BaseModel):
    file_hash: Optional[str] = Field(
        default=None,
        description="Hash of source file",
    )
    section_id: Optional[str] = Field(
        default=None,
        description="Section ID",
    )
    chunk_id: Optional[int] = Field(
        default=None,
        ge=0,
        description="Chunk ID",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Number of points to return",
    )
    qdrant_url: Optional[str] = Field(
        default=None,
        description="Qdrant Service URL (empty = default from env)",
    )


@router.get("/collections")
def api_list_collections(
    qdrant_url: Optional[str] = Query(None, description="Qdrant Service URL (empty = default)"),
    user=Depends(verify_token),
):
    """
    List of collections in Qdrant
    (for Qdrant Inspector – read-only)
    """
    return {
        "collections": list_collections(qdrant_url=qdrant_url)
    }


@router.get("/collections/{name}")
def api_get_collection_detail(
    name: str,
    qdrant_url: Optional[str] = Query(None, description="Qdrant Service URL (empty = default)"),
    user=Depends(verify_token),
):
    """
    Detailed info for a collection
    """
    return get_collection_detail(name, qdrant_url=qdrant_url)


@router.get("/collections/{name}/points")
def api_list_points(
    name: str,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Points per load",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Offset for scroll",
    ),
    qdrant_url: Optional[str] = Query(None, description="Qdrant Service URL (empty = default)"),
    user=Depends(verify_token),
):
    """
    Scroll through points (read-only)
    """
    return {
        "points": list_points(
            collection=name,
            limit=limit,
            offset=offset,
            qdrant_url=qdrant_url,
        )
    }


@router.post("/collections/{name}/filter")
def api_filter_points(
    name: str,
    req: QdrantFilterRequest,
    user=Depends(verify_token),
):
    """
    Filter points by payload metadata
    """
    return {
        "points": filter_points(
            collection=name,
            file_hash=req.file_hash,
            section_id=req.section_id,
            chunk_id=req.chunk_id,
            limit=req.limit,
            qdrant_url=req.qdrant_url,
        )
    }
