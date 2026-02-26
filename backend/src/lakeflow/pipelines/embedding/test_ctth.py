# curl -X POST https://research.neu.edu.vn/ollama/api/embed \
#   -H "Content-Type: application/json" \
#   -d '{
#     "model": "qwen3-embedding",
#     "input": "Apple"
#   }'

print('adsf')
import requests
import json

url = "https://research.neu.edu.vn/ollama/api/embed"

payload = {
    "model": "qwen3-embedding",
    "input": "Apple"
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Báo lỗi nếu HTTP != 200

    data = response.json()
    print("Response JSON:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

except requests.exceptions.RequestException as e:
    print("Request failed:", e)