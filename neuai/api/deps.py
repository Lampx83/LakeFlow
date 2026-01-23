from functools import lru_cache
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "neuai_chunks"


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
    )


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )
