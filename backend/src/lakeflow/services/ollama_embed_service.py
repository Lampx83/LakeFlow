import os
import requests
from typing import List

OLLAMA_EMBED_URL = os.getenv(
    "OLLAMA_EMBED_URL",
    "https://research.neu.edu.vn/ollama/api/embed"
)

EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "qwen3-embedding:8b"
)


def embed_batch(texts: List[str]) -> List[List[float]]:
    """
    Embed multiple texts via Ollama.
    Returns: List of vectors
    """

    payload = {
        "model": EMBED_MODEL,
        "input": texts
    }

    response = requests.post(
        OLLAMA_EMBED_URL,
        json=payload,
        timeout=120
    )

    if response.status_code != 200:
        raise RuntimeError(f"Ollama embed error: {response.text}")

    data = response.json()

    if "embeddings" in data:
        return data["embeddings"]

    if "embedding" in data:
        return [data["embedding"]]

    raise RuntimeError("Unexpected embedding format from Ollama")