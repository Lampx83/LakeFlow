from qdrant_client import QdrantClient
from eduai.core.config import QDRANT_URL, QDRANT_API_KEY


_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """
    Singleton Qdrant client cho toàn backend
    """
    global _client
    if _client is None:
        _client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )
    return _client
