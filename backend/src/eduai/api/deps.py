from functools import lru_cache
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import os

COLLECTION_NAME = "eduai_chunks"


@lru_cache
def get_qdrant_client():
    from qdrant_client import QdrantClient

    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))


    return client

@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )
