# frontend/streamlit/services/qdrant_service.py

import requests
from typing import List, Dict, Any, Optional

from config.settings import API_BASE


# =====================================================
# INTERNAL
# =====================================================

def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# =====================================================
# COLLECTIONS
# =====================================================

def list_collections(token: str, qdrant_url: Optional[str] = None):
    params = {}
    if qdrant_url:
        params["qdrant_url"] = qdrant_url
    resp = requests.get(
        f"{API_BASE}/qdrant/collections",
        params=params,
        headers=_headers(token),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["collections"]




def get_collection_detail(
    collection: str,
    token: str,
    qdrant_url: Optional[str] = None,
) -> Dict[str, Any]:
    params = {}
    if qdrant_url:
        params["qdrant_url"] = qdrant_url
    resp = requests.get(
        f"{API_BASE}/qdrant/collections/{collection}",
        params=params,
        headers=_headers(token),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


# =====================================================
# POINTS – BROWSE
# =====================================================

def list_points(
    collection: str,
    token: str,
    *,
    limit: int = 50,
    offset: int = 0,
    qdrant_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    params = {"limit": limit, "offset": offset}
    if qdrant_url:
        params["qdrant_url"] = qdrant_url
    resp = requests.get(
        f"{API_BASE}/qdrant/collections/{collection}/points",
        params=params,
        headers=_headers(token),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["points"]


# =====================================================
# POINTS – FILTER
# =====================================================

def filter_points(
    collection: str,
    token: str,
    *,
    file_hash: Optional[str] = None,
    section_id: Optional[str] = None,
    chunk_id: Optional[int] = None,
    limit: int = 50,
    qdrant_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    payload = {
        "file_hash": file_hash,
        "section_id": section_id,
        "chunk_id": chunk_id,
        "limit": limit,
    }
    if qdrant_url:
        payload["qdrant_url"] = qdrant_url

    resp = requests.post(
        f"{API_BASE}/qdrant/collections/{collection}/filter",
        json=payload,
        headers=_headers(token),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["points"]
