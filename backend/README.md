# LakeFlow Backend

FastAPI backend and data pipelines for [LakeFlow](https://github.com/Lampx83/EDUAI): ingest, staging, processing, embedding, and semantic search.

---

## Overview

- **API:** FastAPI app (`lakeflow.main:app`) — auth, search, embed, pipeline trigger, Qdrant proxy, system.
- **Data Lake:** Layered zones under `LAKEFLOW_DATA_BASE_PATH`: `000_inbox` → `100_raw` → `200_staging` → `300_processed` → `400_embeddings` → `500_catalog`.
- **Vector store:** Qdrant (default collection `lakeflow_chunks`). Embeddings via sentence-transformers (e.g. `all-MiniLM-L6-v2`).

---

## Requirements

- Python ≥ 3.10
- Qdrant (e.g. Docker: `docker compose up -d qdrant`)
- See `requirements.txt` for Python dependencies

---

## Install & run

**Với Docker** (từ thư mục gốc repo LakeFlow, nơi có `docker-compose.yml`):

```bash
docker compose up --build
# API: http://localhost:8011
```

**Local dev** (từ thư mục gốc repo, vào `backend`):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
# Tạo/copy .env (repo root hoặc backend) với LAKEFLOW_DATA_BASE_PATH, QDRANT_HOST, v.v.
python -m uvicorn lakeflow.main:app --reload --port 8011
```

- Nếu gặp lỗi **`bad interpreter`** (venv trỏ sai Python): xóa `.venv`, chạy lại `python3 -m venv .venv` rồi `pip install -r requirements.txt` và `pip install -e .`.
- Nếu báo **`Address already in use`** (cổng 8011 đã bị chiếm): giải phóng rồi chạy lại server — `lsof -ti :8011 | xargs kill -9`

- **Swagger:** http://localhost:8011/docs  
- **ReDoc:** http://localhost:8011/redoc  
- **Embed API:** [docs/API_EMBED.md](docs/API_EMBED.md) — `POST /search/embed`

---

## Pipeline steps (CLI)

Chạy từ thư mục **backend** (đã kích hoạt venv và set `LAKEFLOW_DATA_BASE_PATH` trong `.env` hoặc môi trường).

| Step | Command | Output |
|------|---------|--------|
| 0 – Inbox → Raw | `python -m lakeflow.scripts.step0_inbox` | Hash, dedup, catalog |
| 1 – Staging | `python -m lakeflow.scripts.step1_raw` | `pdf_profile.json`, `validation.json` |
| 2 – Processed | `python -m lakeflow.scripts.step2_staging` | `clean_text.txt`, `chunks.json`, `tables.json` |
| 3 – Embeddings | `python -m lakeflow.scripts.step3_processed_files` | `embeddings.npy`, `chunks_meta.json` |
| 4 – Qdrant | `python -m lakeflow.scripts.step3_processed_qdrant` | Points in Qdrant |

Hoặc dùng **Streamlit UI** (Pipeline Runner) khi `LAKEFLOW_MODE=DEV`.

---

## Main APIs

- **POST /auth/login** – Demo login (e.g. `admin` / `admin123`), returns JWT.
- **POST /search/embed** – Body `{"text": "..."}` → `vector`, `embedding`, `dim`.
- **POST /search/semantic** – Body `{"query": "...", "top_k": 5, "qdrant_url": "...", "collection_name": "..."}`.
- **POST /search/qa** – RAG-style Q&A (semantic search + LLM). Optional.
- **POST /pipeline/run** – Run a pipeline step (auth required).
- **GET/POST /qdrant/** – Qdrant collections and points (proxy).

---

## Design notes

- **Idempotent** pipelines; deterministic UUIDs for Qdrant.
- **SQLite** without WAL (NAS-friendly).
- **No full-file load** for large files; streaming where applicable.

---

## License

Same as the root repository.
