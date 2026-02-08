# API Vector hóa chuỗi (Embed)

API cho phép vector hóa (embed) một chuỗi văn bản, dùng cùng model với Semantic Search (`sentence-transformers/all-MiniLM-L6-v2`). Vector trả về đã được chuẩn hóa (normalized), phù hợp so sánh cosine similarity.

---

## Endpoint

| Thuộc tính | Giá trị |
|------------|--------|
| **Method** | `POST` |
| **URL** | `/search/embed` |
| **Content-Type** | `application/json` |

**Base URL:** `http://localhost:8011` (DEV) hoặc URL backend của bạn.

---

## Request

### Body (JSON)

| Trường | Kiểu | Bắt buộc | Mô tả |
|--------|------|----------|--------|
| `text` | string | Có | Chuỗi cần vector hóa. Không được rỗng. |

### Ví dụ

```json
{
  "text": "Quy định về tuyển sinh đại học"
}
```

---

## Response

### Thành công (200 OK)

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `text` | string | Chuỗi đã gửi (echo). |
| `vector` | array of float | Vector embedding (đã normalize). |
| `embedding` | array of float | Cùng giá trị với `vector` (alias cho client đọc `embedding`). |
| `dim` | integer | Số chiều của vector (384 với model mặc định). |

### Ví dụ response

```json
{
  "text": "Quy định về tuyển sinh đại học",
  "vector": [0.012, -0.034, 0.056, ...],
  "embedding": [0.012, -0.034, 0.056, ...],
  "dim": 384
}
```

---

## Cách gọi

### cURL

```bash
curl -X POST "http://localhost:8011/search/embed" \
  -H "Content-Type: application/json" \
  -d '{"text": "Quy định về tuyển sinh đại học"}'
```

### Python (requests)

```python
import requests

url = "http://localhost:8011/search/embed"
payload = {"text": "Quy định về tuyển sinh đại học"}
resp = requests.post(url, json=payload, timeout=10)
data = resp.json()
print("Dim:", data["dim"])
print("Vector (5 số đầu):", data["vector"][:5])
```

### JavaScript (fetch)

```javascript
const res = await fetch("http://localhost:8011/search/embed", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "Quy định về tuyển sinh đại học" }),
});
const data = await res.json();
console.log("Dim:", data.dim);
```

---

## Lưu ý

- **Model:** Mặc định dùng `sentence-transformers/all-MiniLM-L6-v2` (384 chiều). Cùng model với Semantic Search và pipeline embedding của EDUAI.
- **Chuẩn hóa:** Vector trả về đã được normalize (L2), dùng trực tiếp để tính cosine similarity với các vector trong Qdrant.
- **Xác thực:** Hiện endpoint không bắt buộc Bearer token. Nếu backend bật auth toàn cục thì cần gửi header `Authorization: Bearer <token>`.
- **Giới hạn:** Không giới hạn độ dài chuỗi; model cắt theo giới hạn token của nó (tối đa 512 token với MiniLM).

---

## Tích hợp với hệ thống bên ngoài

API này có thể dùng làm **embedding service** cho hệ thống khác (ví dụ Research Chat, admin Qdrant search):

- **Request:** `POST`, body `{ "text": "chuỗi cần embed" }`.
- **Response:** JSON có trường `vector` (và `embedding` – alias của `vector`) là mảng số thực.

Ví dụ cấu hình ở hệ thống gọi tới EDUAI:

- Biến môi trường: `REGULATIONS_EMBEDDING_URL=http://localhost:8011/search/embed` (DEV) hoặc URL backend EDUAI khi deploy.
- Gửi: `POST` với `Content-Type: application/json`, body `{ "text": "<keyword>" }`.
- Đọc vector từ response: `response.embedding` hoặc `response.vector` (cùng nội dung).

Client nên có timeout hợp lý (ví dụ 25s) khi gọi embedding.

---

## Swagger / OpenAPI

Khi chạy backend, xem thêm tất cả API tại:

- **Swagger UI:** `http://localhost:8011/docs`
- **ReDoc:** `http://localhost:8011/redoc`

Endpoint `/search/embed` nằm trong nhóm **Search**.
