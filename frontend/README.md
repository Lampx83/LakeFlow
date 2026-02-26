# LakeFlow Streamlit UI

Streamlit **control & test UI** for [LakeFlow](https://github.com/Lampx83/EDUAI): run pipelines, explore the data lake, and try semantic search.

---

## Purpose

- **Test & debug** the LakeFlow backend API
- **Run pipeline steps** (when `LAKEFLOW_MODE=DEV`)
- **Semantic search** and **Qdrant Explorer**
- **Data Lake Explorer** — browse zones `000_inbox` … `500_catalog`

This UI is for **operators and developers**, not for end-users or production-facing use. It has no fine-grained permissions and shows tokens; use only in dev or trusted internal networks.

---

## Requirements

- LakeFlow **backend** running (e.g. http://localhost:8011 or `lakeflow-backend:8011` in Docker)
- Qdrant (e.g. `docker compose up -d qdrant` or shared Qdrant URL)

---

## Run with Docker (recommended)

From the **repo root**:

```bash
docker compose up --build
```

- **Streamlit:** http://localhost:8012 (or the port mapped in `docker-compose.yml`)
- **Login:** `admin` / `admin123` (demo)

Ensure `.env` in repo root has at least `API_BASE_URL`, `LAKEFLOW_DATA_BASE_PATH`, and (if needed) `QDRANT_HOST` / `QDRANT_PORT`. For Docker, `API_BASE_URL=http://lakeflow-backend:8011` and `LAKEFLOW_DATA_BASE_PATH=/data` are typical.

---

## Run locally (dev)

1. **Backend** and **Qdrant** must be running (see [backend/README.md](../backend/README.md)).
2. From repo root, create/use `.env` with `API_BASE_URL=http://localhost:8011`, `LAKEFLOW_DATA_BASE_PATH=/path/to/your/data/lake`, and optional `QDRANT_HOST=localhost`.
3. Chạy Streamlit (bắt buộc ở thư mục **frontend/streamlit** — file `requirements.txt` nằm tại đây):

   **Cách A — Dùng venv (khuyến nghị, tránh lỗi quyền khi cài package):**

   ```bash
   cd frontend/streamlit
   python3 -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   export $(grep -v '^#' ../../.env | xargs)
   streamlit run app.py
   ```

   **Cách B — Từ repo root** (cần đã cài streamlit): `python frontend/streamlit/dev_with_reload.py` (tự load `.env`).

- Mặc định: http://localhost:8501 (trừ khi đổi trong config).

---

## Main features

| Feature | Description |
|--------|-------------|
| **Login** | Demo auth; JWT used for API calls |
| **Semantic Search** | Query text → results from Qdrant (choose or type Qdrant URL) |
| **Qdrant Inspector** | List collections, browse points |
| **Pipeline Runner** | Run pipeline steps (only if `LAKEFLOW_MODE=DEV`) |
| **Data Lake Explorer** | Browse files in each zone; preview JSON/TXT |

---

## Configuration

- **Backend URL:** `API_BASE_URL` (e.g. `http://lakeflow-backend:8011` in Docker, `http://localhost:8011` locally).
- **Data lake path:** `LAKEFLOW_DATA_BASE_PATH` (e.g. `/data` in Docker).
- **Qdrant:** Defaults from backend; you can pick or type a Qdrant URL in the UI for search and inspector.
- **Pipeline Runner:** Shown only when `LAKEFLOW_MODE=DEV`. Do not enable in production.

---

## Project layout

```
frontend/streamlit/
├── app.py              # Entrypoint
├── config/settings.py  # API base, LAKEFLOW_MODE, Qdrant options
├── pages/              # Semantic Search, QA, Pipeline Runner, Data Lake Explorer, etc.
├── services/           # API client, pipeline, Qdrant
├── state/              # Session, token storage
├── requirements.txt
└── README.md
```

---

## License

Same as the root repository.
