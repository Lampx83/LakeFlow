from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from lakeflow.core.config import get_qdrant_url, QDRANT_API_KEY


# ==============================================# =====================================================

_client: Optional[QdrantClient] = None


def get_client(qdrant_url: Optional[str] = None) -> QdrantClient:
    """Client Qdrant. Nếu qdrant_url truyền vào thì dùng URL đó (không cache); không thì dùng mặc định từ env."""
    global _client
    if qdrant_url and (s := qdrant_url.strip()):
        url = s if s.startswith("http://") or s.startswith("https://") else f"http://{s}"
        return QdrantClient(url=url, api_key=QDRANT_API_KEY)
    if _client is None:
        _client = QdrantClient(
            url=get_qdrant_url(None),
            api_key=QDRANT_API_KEY,
        )
    return _client


# =====================================================
# COLLECTIONS
# =====================================================

def list_collections(qdrant_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Danh sách collections trong Qdrant
    """
    client = get_client(qdrant_url)
    resp = client.get_collections()

    return [
        {
            "name": c.name,
        }
        for c in resp.collections
    ]


def _infer_payload_schema(client: QdrantClient, collection: str, sample_size: int = 200) -> Dict[str, str]:
    """
    Suy luận schema payload từ mẫu points (key -> kiểu: string, integer, number, boolean, array, object).
    """
    schema: Dict[str, str] = {}
    try:
        points, _ = client.scroll(
            collection_name=collection,
            limit=sample_size,
            with_payload=True,
            with_vectors=False,
        )
    except Exception:
        return {}

    def type_name(v: Any) -> str:
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "boolean"
        if isinstance(v, int):
            return "integer"
        if isinstance(v, float):
            return "number"
        if isinstance(v, str):
            return "string"
        if isinstance(v, list):
            return "array"
        if isinstance(v, dict):
            return "object"
        return "string"

    for p in points:
        payload = p.payload or {}
        for key, val in payload.items():
            t = type_name(val)
            if key not in schema:
                schema[key] = t
            elif schema[key] != t:
                # Nhiều kiểu khác nhau → dùng union hoặc "string" an toàn
                schema[key] = "string"
    return schema


def get_collection_detail(name: str, qdrant_url: Optional[str] = None) -> Dict[str, Any]:
    client = get_client(qdrant_url)
    info = client.get_collection(name)

    vectors = {}
    params = info.config.params.vectors

    # Trường hợp 1: single vector
    if hasattr(params, "size"):
        vectors = {
            "default": {
                "size": params.size,
                "distance": str(params.distance),
            }
        }

    # Trường hợp 2: named vectors
    elif isinstance(params, dict):
        for k, v in params.items():
            vectors[k] = {
                "size": v.size,
                "distance": str(v.distance),
            }

    payload_schema = _infer_payload_schema(client, name) if info.points_count else {}

    return {
        "name": name,
        "status": info.status,
        "vectors": vectors,   # ✅ JSON-safe
        "points_count": info.points_count,
        "indexed_vectors_count": info.indexed_vectors_count,
        "segments_count": info.segments_count,
        "payload_schema": payload_schema,
    }




# =====================================================
# POINTS – BROWSE
# =====================================================

def list_points(
    collection: str,
    *,
    limit: int = 50,
    offset: int = 0,
    qdrant_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Duyệt points theo offset/limit (debug, inspector)
    """
    client = get_client(qdrant_url)

    points, _ = client.scroll(
        collection_name=collection,
        limit=limit,
        offset=offset,
        with_payload=True,
        with_vectors=False,  # inspector: không cần vector
    )

    return [_serialize_point(p) for p in points]


# =====================================================
# POINTS – FILTER
# =====================================================

def filter_points(
    collection: str,
    *,
    file_hash: Optional[str] = None,
    section_id: Optional[str] = None,
    chunk_id: Optional[int] = None,
    limit: int = 50,
    qdrant_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter points theo metadata payload
    """
    must: List[qmodels.FieldCondition] = []

    if file_hash:
        must.append(
            qmodels.FieldCondition(
                key="file_hash",
                match=qmodels.MatchValue(value=file_hash),
            )
        )

    if section_id:
        must.append(
            qmodels.FieldCondition(
                key="section_id",
                match=qmodels.MatchValue(value=section_id),
            )
        )

    if chunk_id is not None:
        must.append(
            qmodels.FieldCondition(
                key="chunk_id",
                match=qmodels.MatchValue(value=chunk_id),
            )
        )

    flt = qmodels.Filter(must=must) if must else None

    client = get_client(qdrant_url)

    points, _ = client.scroll(
        collection_name=collection,
        scroll_filter=flt,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    return [_serialize_point(p) for p in points]


# =====================================================
# INTERNAL
# =====================================================

def _serialize_point(p) -> Dict[str, Any]:
    """
    Chuẩn hoá point để trả về API / UI
    """
    return {
        "id": p.id,
        "score": getattr(p, "score", None),
        "payload": p.payload or {},
    }
