# Text Vectorization (Embed) API

API for vectorizing (embedding) a text string, using the same model as Semantic Search (`sentence-transformers/all-MiniLM-L6-v2`). Returned vectors are normalized and suitable for cosine similarity comparison.

---

## Endpoint

| Property | Value |
|----------|-------|
| **Method** | `POST` |
| **URL** | `/search/embed` |
| **Content-Type** | `application/json` |

**Base URL:** `http://localhost:8011` (DEV) or your backend URL.

---

## Request

### Body (JSON)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text to vectorize. Must not be empty. |

### Example

```json
{
  "text": "University admission regulations"
}
```

---

## Response

### Success (200 OK)

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Echo of the text sent. |
| `vector` | array of float | Vector embedding (normalized). |
| `embedding` | array of float | Same as `vector` (alias for clients reading `embedding`). |
| `dim` | integer | Vector dimension (384 with default model). |

### Example response

```json
{
  "text": "University admission regulations",
  "vector": [0.012, -0.034, 0.056, ...],
  "embedding": [0.012, -0.034, 0.056, ...],
  "dim": 384
}
```

---

## Usage

### cURL

```bash
curl -X POST "http://localhost:8011/search/embed" \
  -H "Content-Type: application/json" \
  -d '{"text": "University admission regulations"}'
```

### Python (requests)

```python
import requests

url = "http://localhost:8011/search/embed"
payload = {"text": "University admission regulations"}
resp = requests.post(url, json=payload, timeout=10)
data = resp.json()
print("Dim:", data["dim"])
print("Vector (first 5):", data["vector"][:5])
```

### JavaScript (fetch)

```javascript
const res = await fetch("http://localhost:8011/search/embed", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "University admission regulations" }),
});
const data = await res.json();
console.log("Dim:", data.dim);
```

---

## Notes

- **Model:** Default is `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). Same model as Semantic Search and LakeFlow embedding pipeline.
- **Normalization:** Returned vectors are L2-normalized and can be used directly for cosine similarity with Qdrant vectors.
- **Authentication:** Endpoint does not require Bearer token by default. If global auth is enabled, send header `Authorization: Bearer <token>`.
- **Limits:** No limit on input length; model truncates to its token limit (max 512 tokens for MiniLM).

---

## Integration with external systems

This API can serve as an **embedding service** for other systems (e.g. Research Chat, admin Qdrant search):

- **Request:** `POST` with body `{ "text": "<string to embed>" }`.
- **Response:** JSON with `vector` (and `embedding` – alias of `vector`) as an array of floats.

Example configuration for a system calling LakeFlow:

- Environment variable: `REGULATIONS_EMBEDDING_URL=http://localhost:8011/search/embed` (DEV) or LakeFlow backend URL when deployed.
- Send: `POST` with `Content-Type: application/json`, body `{ "text": "<keyword>" }`.
- Read vector from response: `response.embedding` or `response.vector` (same content).

Clients should use a reasonable timeout (e.g. 25s) when calling the embedding endpoint.

---

## Swagger / OpenAPI

When the backend is running, see all APIs at:

- **Swagger UI:** `http://localhost:8011/docs`
- **ReDoc:** `http://localhost:8011/redoc`

Endpoint `/search/embed` is in the **Search** group.
