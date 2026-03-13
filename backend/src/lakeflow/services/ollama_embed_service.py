import os
import requests
from typing import List

import lakeflow.config.env  # noqa: F401 - load .env before config
from lakeflow.core.config import LLM_BASE_URL

OLLAMA_EMBED_URL = (
    os.getenv("OLLAMA_EMBED_URL") or f"{LLM_BASE_URL.rstrip('/')}/api/embed"
)

EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "qwen3-embedding:8b"
)


def embed_batch(texts: List[str], model: str | None = None) -> List[List[float]]:
    """
    Embed multiple texts via Ollama.

    Args:
        texts: List of strings to embed
        model: Override model (optional). If None, uses EMBED_MODEL env or default.

    Returns:
        List of vectors
    """
    use_model = (model or "").strip() or EMBED_MODEL

    payload = {
        "model": use_model,
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