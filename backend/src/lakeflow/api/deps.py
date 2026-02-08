import os
from functools import lru_cache

from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "lakeflow_chunks"


@lru_cache
def get_qdrant_client():
    from qdrant_client import QdrantClient

    return QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )
