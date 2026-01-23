from pathlib import Path
from typing import List, Dict, Any
import uuid

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    VectorParams,
    Distance,
)

from neuai.common.jsonio import read_json


# =========================
# Qdrant collection config
# =========================

COLLECTION_NAME = "neuai_chunks"


# =========================
# Collection management
# =========================

def ensure_collection(
    client: QdrantClient,
    vector_dim: int,
) -> None:
    """
    Tạo collection nếu chưa tồn tại.
    """
    collections = client.get_collections().collections
    if any(c.name == COLLECTION_NAME for c in collections):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_dim,
            distance=Distance.COSINE,
        ),
    )


# =========================
# Ingest embeddings
# =========================

def ingest_file_embeddings(
    client: QdrantClient,
    file_hash: str,
    embeddings_dir: Path,
) -> int:
    """
    Ingest embeddings của một file_hash vào Qdrant.

    Parameters
    ----------
    client : QdrantClient
        Client đã kết nối Qdrant
    file_hash : str
        Hash của file (định danh logic)
    embeddings_dir : Path
        Thư mục 400_embeddings/<file_hash>

    Returns
    -------
    int
        Số vector đã ingest
    """

    embeddings_file = embeddings_dir / "embeddings.npy"
    meta_file = embeddings_dir / "chunks_meta.json"

    if not embeddings_file.exists():
        raise FileNotFoundError(
            f"Missing embeddings.npy for {file_hash}"
        )

    if not meta_file.exists():
        raise FileNotFoundError(
            f"Missing chunks_meta.json for {file_hash}"
        )

    vectors = np.load(embeddings_file)
    chunks_meta: List[Dict[str, Any]] = read_json(meta_file)

    if len(vectors) != len(chunks_meta):
        raise RuntimeError(
            f"Vector count mismatch for {file_hash}: "
            f"{len(vectors)} vectors vs {len(chunks_meta)} meta"
        )

    points: List[PointStruct] = []

    for vec, meta in zip(vectors, chunks_meta):
        # -------------------------
        # Deterministic UUID (Qdrant-safe)
        # -------------------------
        point_id = uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"{file_hash}:{meta['chunk_id']}"
        )

        payload = {
            "file_hash": file_hash,
            "chunk_id": meta["chunk_id"],
            "section_id": meta.get("section_id"),
            "token_estimate": meta.get("token_estimate"),
            "source": "NEUAI",
        }

        points.append(
            PointStruct(
                id=point_id,
                vector=vec.tolist(),
                payload=payload,
            )
        )

    # -------------------------
    # Upsert into Qdrant
    # -------------------------
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    return len(points)