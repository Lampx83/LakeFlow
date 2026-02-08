# LakeFlow

**Data Lake pipelines for Vector DB & AI.** Ingest raw documents, run staged pipelines, and produce embeddings + semantic search—ready for RAG, LLM, and analytics.

[![CI](https://github.com/Lampx83/EDUAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Lampx83/EDUAI/actions/workflows/ci.yml)

---

## What is LakeFlow?

LakeFlow is an open-source platform that turns your **Data Lake** into a structured pipeline:

- **Ingest** raw files (PDF, Excel, etc.) with hash, dedup, and catalog
- **Stage** and **process** into clean text, chunks, and tables
- **Embed** with sentence-transformers and store vectors in **Qdrant**
- Expose **Semantic Search API** and **embedding endpoint** for RAG, LLM, and downstream apps

All components run via **Docker** by default—no need to install Python or heavy dependencies on the host.

---

## Features

- **Layered Data Lake** – Zones: `000_inbox` → `100_raw` → `200_staging` → `300_processed` → `400_embeddings` → `500_catalog`
- **Idempotent pipelines** – Re-run safely; deterministic UUIDs for Qdrant
- **Semantic search** – Query in natural language; results by cosine similarity
- **Embedding API** – `POST /search/embed` for text→vector (compatible with external RAG/LLM services)
- **Streamlit control UI** – Run pipelines, explore data lake, test search (dev/internal use)
- **Multi–Qdrant support** – Choose or type a Qdrant URL in the UI
- **NAS-friendly** – SQLite without WAL; works on Synology/NFS

---

## Quick start (Docker)

**Requirements:** Docker ≥ 20.x, Docker Compose ≥ 2.x

```bash
git clone https://github.com/Lampx83/EDUAI.git LakeFlow
cd LakeFlow
cp .env.example .env
# Edit .env: set LAKEFLOW_DATA_BASE_PATH to a directory that will hold the data lake (or leave /data for Docker volume)
docker compose up --build
```

- **Backend API:** http://localhost:8011  
- **API docs:** http://localhost:8011/docs  
- **Streamlit UI:** http://localhost:8012 (login: `admin` / `admin123`)

Data lake root is the `lakeflow_data` volume (or path you set). Create zones manually if needed: `000_inbox`, `100_raw`, `200_staging`, `300_processed`, `400_embeddings`, `500_catalog`.

---

## Project structure

```
LakeFlow/
├── backend/           # FastAPI app + pipeline scripts (Python)
│   ├── src/lakeflow/  # Main package
│   ├── docs/          # API docs (e.g. API_EMBED.md)
│   └── README.md
├── frontend/
│   └── streamlit/     # Streamlit control UI
│       └── README.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Description |
|----------|-------------|
| `LAKEFLOW_DATA_BASE_PATH` | Root path for the data lake (e.g. `/data` in Docker, or a host path) |
| `LAKEFLOW_MODE` | `DEV` = show Pipeline Runner in UI; omit or other = hide |
| `QDRANT_HOST` | Qdrant host (e.g. `lakeflow-qdrant` in Docker, `localhost` when running Qdrant alone) |
| `API_BASE_URL` | Backend URL (e.g. `http://lakeflow-backend:8011` in Docker, `http://localhost:8011` for local dev) |

See `.env.example` for a full template.

---

## Development (without Docker)

1. **Backend** (from repo root):
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt && pip install -e .
   # Ensure .env is in repo root with LAKEFLOW_DATA_BASE_PATH, QDRANT_HOST, API_BASE_URL
   python -m uvicorn lakeflow.main:app --reload --port 8011
   ```
2. **Qdrant** (if needed): `docker compose up -d qdrant`
3. **Frontend**: From repo root, load `.env` then run `python frontend/streamlit/dev_with_reload.py` or `streamlit run frontend/streamlit/app.py`.

Pipeline Runner in the UI is only shown when `LAKEFLOW_MODE=DEV`.

---

## API overview

- **Health:** `GET /health`
- **Auth (demo):** `POST /auth/login` (e.g. `admin` / `admin123`)
- **Embed:** `POST /search/embed` — body `{"text": "..."}` → returns `vector` / `embedding` and `dim`
- **Semantic search:** `POST /search/semantic` — body `{"query": "...", "top_k": 5}` (optional `qdrant_url`, `collection_name`)

See [backend/README.md](backend/README.md) and [backend/docs/API_EMBED.md](backend/docs/API_EMBED.md) for details.

---

## CI / CD

- **CI** (`.github/workflows/ci.yml`): On push/PR to `main` or `develop` — lint (Ruff) and Docker build for backend and frontend.
- **CD** (`.github/workflows/cd.yml`): On release (tag) — build and push images to GitHub Container Registry.

Do not commit `.env`; use `.env.example` as reference.

---

## Deployment

- Run on VPS, on-prem, or cloud (e.g. AWS, GCP, Azure).
- Use `docker compose up -d` (or `docker compose up -d --build`) to run all services; configure `.env` on the server (e.g. `LAKEFLOW_DATA_BASE_PATH`, `QDRANT_HOST`, `API_BASE_URL`).
- Optional: configure GitHub Actions deploy workflow (e.g. SSH deploy on push to `main`); see workflow comments and repo docs.

---

## Contributing

Contributions are welcome: issues, pull requests, and documentation improvements. Please open an issue first for large changes.

---

## License

See the [LICENSE](LICENSE) file in this repository (if present). Otherwise, use and modification are at your own responsibility; consider adding a license before public use.
