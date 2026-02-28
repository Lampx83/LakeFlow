import requests

from lakeflow.services.ollama_embed_service import OLLAMA_EMBED_URL, EMBED_MODEL

url = OLLAMA_EMBED_URL

payload = {
    "model": EMBED_MODEL,
    "input": ["Xin chào"]
}

resp = requests.post(url, json=payload)
data = resp.json()

embedding = data.get("embedding") or data.get("embeddings")[0]

print("Vector length:", len(embedding))