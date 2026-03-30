from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import uuid

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    VectorParams,
    Distance,
)

from lakeflow.common.jsonio import read_json
from lakeflow.common.nas_io import (
    nas_safe_copy,
    nas_safe_find_processed_dir,
)
from lakeflow.vectorstore.constants import COLLECTION_NAME


def _default_vector_size(client: QdrantClient, collection_name: str) -> Optional[int]:
    """Return configured size for the default (unnamed) vector, or None if missing."""
    try:
        info = client.get_collection(collection_name)
    except Exception:
        return None
    params = info.config.params.vectors
    if hasattr(params, "size"):
        return int(params.size)
    if isinstance(params, dict) and params:
        first = next(iter(params.values()))
        return int(first.size)
    return None


def ensure_collection(
    client: QdrantClient,
    vector_dim: int,
    collection_name: Optional[str] = None,
) -> None:
    """
    Ensure Qdrant collection exists with vector_dim matching embedding.npy.

    If the collection already exists but was created with a different vector size
    (e.g. switched from 384-dim to 4096-dim embed model), delete and recreate so
    upsert does not fail with "expected dim: X, got Y".
    collection_name: collection name; None = use default COLLECTION_NAME.
    """
    name = (collection_name or "").strip() or COLLECTION_NAME

    collections = client.get_collections().collections
    exists = any(c.name == name for c in collections)

    if exists:
        existing_dim = _default_vector_size(client, name)
        if existing_dim is not None and existing_dim == vector_dim:
            return
        if existing_dim is not None and existing_dim != vector_dim:
            print(
                f"[QDRANT] Collection {name!r}: stored vectors are dim={existing_dim}, "
                f"new embeddings are dim={vector_dim}. Deleting and recreating collection."
            )
            client.delete_collection(collection_name=name)
        else:
            raise RuntimeError(
                f"Collection {name!r} already exists but vector size could not be determined; "
                f"delete it in Qdrant or use another collection name."
            )

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=vector_dim,
            distance=Distance.COSINE,
        ),
    )


def ingest_file_embeddings(
    client: QdrantClient,
    file_hash: str,
    embeddings_dir: Path,
    processed_root: Path,
    collection_name: Optional[str] = None,
    parent_dir: Optional[str] = None,
) -> int:
    """
    Ingest embeddings of one file into Qdrant.

    parent_dir: domain name (parent dir in 400_embeddings); if set, avoids iterdir on NAS.
    collection_name: collection name; None = use default COLLECTION_NAME.

    Source of truth:
    - Vectors + meta: 400_embeddings/<domain>/<file_hash> or 400_embeddings/<file_hash>
    - Text chunks   : 300_processed/<domain>/<file_hash>/chunks.json or 300_processed/<file_hash>/chunks.json

    Returns
    -------
    int
        Number of vectors ingested
    """
    coll_name = (collection_name or "").strip() or COLLECTION_NAME

    processed_dir = nas_safe_find_processed_dir(processed_root, file_hash, parent_dir=parent_dir)
    if not processed_dir:
        raise FileNotFoundError(
            f"Missing 300_processed dir for {file_hash}"
        )

    embeddings_file = embeddings_dir / "embedding.npy"
    meta_file = embeddings_dir / "chunks_meta.json"
    processed_chunks_file = processed_dir / "chunks.json"

    with tempfile.TemporaryDirectory(prefix="qdrant_ingest_") as tmp:
        tmp = Path(tmp)
        tmp_embed = tmp / "embedding.npy"
        tmp_meta = tmp / "chunks_meta.json"
        tmp_chunks = tmp / "chunks.json"
        nas_safe_copy(embeddings_file, tmp_embed)
        nas_safe_copy(meta_file, tmp_meta)
        nas_safe_copy(processed_chunks_file, tmp_chunks)

        vectors = np.load(tmp_embed)
        chunks_meta: List[Dict[str, Any]] = read_json(tmp_meta)
        chunks: List[Dict[str, Any]] = read_json(tmp_chunks)

    if len(vectors) != len(chunks_meta):
        raise RuntimeError(
            f"Vector/meta count mismatch for {file_hash}: "
            f"{len(vectors)} vectors vs {len(chunks_meta)} meta"
        )

    chunk_text_map = {
        c["chunk_id"]: c.get("text", "")
        for c in chunks
    }

    points: List[PointStruct] = []

    for vec, meta in zip(vectors, chunks_meta):
        chunk_id = meta["chunk_id"]

        # Deterministic UUID (safe for re-run)
        point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{file_hash}:{chunk_id}"
            )
        )

        payload = {
            "file_hash": file_hash,
            "chunk_id": chunk_id,
            "section_id": meta.get("section_id"),
            "token_estimate": meta.get("token_estimate"),
            "text": chunk_text_map.get(chunk_id),  # 🔑 CRITICAL
            "source": "LakeFlow",
        }

        points.append(
            PointStruct(
                id=point_id,
                vector=vec.tolist(),
                payload=payload,
            )
        )

    client.upsert(
        collection_name=coll_name,
        points=points,
    )

    return len(points)
