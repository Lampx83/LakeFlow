import requests

url = "https://research.neu.edu.vn/ollama/api/embed"

payload = {
    "model": "qwen3-embedding:8b",
    "input": "Xin chào"
}

resp = requests.post(url, json=payload)
data = resp.json()

embedding = data.get("embedding") or data.get("embeddings")[0]

print("Vector length:", len(embedding))