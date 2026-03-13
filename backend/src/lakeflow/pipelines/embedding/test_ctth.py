# curl -X POST $LLM_BASE_URL/api/embed (xem .env LLM_BASE_URL)
import requests
import json

from lakeflow.services.ollama_embed_service import OLLAMA_EMBED_URL, EMBED_MODEL

url = OLLAMA_EMBED_URL
payload = {
    "model": EMBED_MODEL,
    "input": ["Apple"]
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise error if HTTP != 200

    data = response.json()
    print("Response JSON:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

except requests.exceptions.RequestException as e:
    print("Request failed:", e)