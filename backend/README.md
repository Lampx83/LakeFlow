# EDUAI – AI Data & Semantic Search Platform

## 1. Giới thiệu

**EDUAI** là nền tảng xử lý dữ liệu và tìm kiếm ngữ nghĩa (Semantic Search) phục vụ các hệ thống AI/LLM nội bộ.
Hệ thống được thiết kế theo kiến trúc **Data Lake nhiều tầng**, hỗ trợ:

* Ingest dữ liệu thô (PDF, Excel, …)
* Phân tích – chuẩn hoá dữ liệu
* Sinh embedding bằng mô hình ngôn ngữ
* Lưu trữ vector trên Qdrant
* Cung cấp API Semantic Search qua FastAPI

Mục tiêu chính:

* Chuẩn hoá pipeline dữ liệu AI
* Dễ mở rộng, dễ audit, dễ bảo trì
* Phù hợp môi trường học thuật & enterprise nội bộ

---

## 2. Kiến trúc tổng thể

### 2.1 Data Lake Zones

```
EDUAI_DATA_BASE_PATH/
├── 000_inbox/        # File đầu vào (theo domain)
├── 100_raw/          # File raw đã hash + deduplicate
├── 200_staging/      # Phân tích & validation
├── 300_processed/    # Dữ liệu AI-ready
├── 400_embeddings/   # Vector embedding
├── 500_catalog/      # SQLite metadata catalog
```

### 2.2 Pipeline tổng quát

```
Inbox
  ↓
Ingestion (hash, dedup, catalog)
  ↓
Staging (file analysis, validation)
  ↓
Processed (clean text, chunks, tables)
  ↓
Embeddings (Sentence-Transformers)
  ↓
Vector Store (Qdrant)
  ↓
Semantic Search API
```

---

## 3. Yêu cầu hệ thống

### 3.1 Phần mềm

* Python **>= 3.10**
* Docker (khuyến nghị)
* Qdrant **>= 1.8**
* OS: Linux / macOS (NAS được hỗ trợ)

### 3.2 Thư viện chính

* FastAPI, Uvicorn
* Pandas, NumPy
* PyPDF2, pdfplumber
* sentence-transformers
* Qdrant Client
* SQLite

Danh sách đầy đủ xem tại: `requirements.txt`

---

## 4. Cấu hình môi trường

### 4.1 File `.env`

Tạo file `.env` tại thư mục gốc dự án:

```env
EDUAI_DATA_BASE_PATH=/absolute/path/to/eduai_data
SECRET_KEY=eduai-secret-key
```

> **Lưu ý:**
>
> * `EDUAI_DATA_BASE_PATH` phải là đường dẫn tuyệt đối
> * Thư mục sẽ được tạo tự động nếu chưa tồn tại

---

## 5. Cài đặt & khởi chạy

### 5.1 Chạy bằng Docker (khuyến nghị)

```bash
docker compose build
docker compose up
```

API sẽ chạy tại:

```
http://localhost:8011
```

Health check:

```
GET /health
```

---

### 5.2 Chạy thủ công (dev mode)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools
python -m pip install -r requirements.txt
python -m pip install -e .

python -m uvicorn eduai.main:app --reload --port 8011

```
Chú ý cần chạy Qdrant (nếu sử dụng)
```
docker compose up qdrant
```
---

### 5.3 API & Tài liệu

* **Swagger UI:** `http://localhost:8011/docs`
* **ReDoc:** `http://localhost:8011/redoc`
* **API Vector hóa chuỗi (Embed):** xem [docs/API_EMBED.md](docs/API_EMBED.md) — `POST /search/embed` để nhận vector embedding của một chuỗi.

---
## 6. Hướng dẫn pipeline dữ liệu

### 6.1 Bước 0 – Ingest Inbox → Raw

```bash
python -m eduai.scripts.step0_inbox
```

Chức năng:

* Hash SHA-256
* Deduplicate
* Copy atomic
* Ghi metadata vào SQLite catalog

---

### 6.2 Bước 1 – Staging (PDF)

```bash
python -m eduai.scripts.step1_raw
```

Sinh:

* `pdf_profile.json`
* `validation.json`

---

### 6.3 Bước 2 – Processed (AI-ready)

```bash
python -m eduai.scripts.step2_staging
```

Sinh:

* `clean_text.txt`
* `sections.json`
* `chunks.json`
* `tables.json`

---

### 6.4 Bước 3 – Embeddings

```bash
python src/eduai/scripts/step3_processed_files.py
```

Sinh:

* `embeddings.npy`
* `chunks_meta.json`
* `model.json`
* `embeddings.jsonl` (debug)

---

### 6.5 Bước 4 – Ingest vào Qdrant

```bash
python src/eduai/scripts/step3_processed_qdrant.py
```

---

## 7. Semantic Search API

### 7.1 Đăng nhập (Demo)

```
POST /auth/login
```

```json
{
  "username": "admin",
  "password": "admin123"
}
```

---

### 7.2 Semantic Search

```
POST /search/semantic
```

```json
{
  "query": "Kinh tế quốc dân",
  "top_k": 5
}
```

Response:

* score
* file_hash
* chunk_id
* section_id
* text
* token_estimate

---

## 8. Lưu ý thiết kế quan trọng

* **Idempotent pipeline**: chạy lại không gây trùng dữ liệu
* **Deterministic UUID** cho Qdrant
* **Không WAL SQLite** (tương thích NAS)
* **Không load toàn bộ file lớn vào memory**
* **Phân tách rõ zone & trách nhiệm**

---

## 9. Định hướng mở rộng

* OCR (Tesseract / PaddleOCR)
* Chunking theo cấu trúc tài liệu
* Metadata-aware search
* RAG pipeline
* User / Role / ACL
* Multi-collection Qdrant
* Audit & lineage tracking

---

## 10. Bản quyền & sử dụng

Dự án phục vụ **nghiên cứu – đào tạo – triển khai nội bộ**.
Không khuyến nghị sử dụng trực tiếp cho môi trường public production khi chưa bổ sung:

* Rate limit
* Auth nâng cao
* Hardening bảo mật

---