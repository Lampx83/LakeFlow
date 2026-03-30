# LakeFlow

**Data Lake pipelines for Vector DB & AI.** Ingest raw documents, run pipelines, produce embeddings — ready for RAG, LLM, semantic search.

**Website:** [lake-flow.vercel.app](https://lake-flow.vercel.app) — docs, API reference, deployment

[![CI](https://github.com/Lampx83/LakeFlow/actions/workflows/ci.yml/badge.svg)](https://github.com/Lampx83/LakeFlow/actions/workflows/ci.yml)

---

## Features

- **Layered Data Lake:** `000_inbox` → `100_raw` → `200_staging` → `300_processed` → `400_embeddings` → `500_catalog`
- **Idempotent pipelines** — Re-run safely, deterministic UUIDs for Qdrant
- **Semantic search** — Natural language query, cosine similarity
- **Embedding API** — `POST /search/embed` for text→vector (RAG/LLM ready)
- **Streamlit UI** — Run pipelines, explore data, test search (dev mode)
- **Multi-Qdrant** — Choose Qdrant URL in UI
- **NAS-friendly** — SQLite without WAL; works on Synology/NFS

---

## Quick start (Docker)

**Requirements:** Docker ≥ 20.x, Docker Compose ≥ 2.x

```bash
git clone https://github.com/Lampx83/LakeFlow.git
cd LakeFlow
cp env.example .env
# Edit .env: HOST_LAKE_PATH, QDRANT_HOST, API_BASE_URL
DOCKER_BUILDKIT=1 docker compose up --build
```

| Service      | URL |
|--------------|-----|
| Backend API  | http://localhost:8011 |
| API docs     | http://localhost:8011/docs |
| Streamlit UI | http://localhost:8012 (login: `admin` / `admin123`) |
| Ollama       | http://localhost:11434 (same stack; backend uses `http://ollama:11434` inside the network) |

Data lake: `lakeflow_data` volume (binds to `HOST_LAKE_PATH` from .env). Create zones if needed: `000_inbox`, `100_raw`, …

**Ollama models (first run):** the stack includes an `ollama` container. Pull models once, e.g.  
`docker exec -it lakeflow-ollama ollama pull qwen3:8b` and `docker exec -it lakeflow-ollama ollama pull qwen3-embedding:8b` (or set `LLM_MODEL` / `EMBED_MODEL` to match what you pull).

**Mac M1 GPU:** Docker runs Linux — no Metal. For GPU, run backend via venv on macOS: `pip install torch` then `pip install -r backend/requirements.txt`.

---

## Configuration

Copy `env.example` to `.env` and adjust:

| Variable      | Description |
|---------------|-------------|
| `HOST_LAKE_PATH` | Host path for data lake (bind to `/data` in container) |
| `LAKE_ROOT`   | Container path (`/data` in Docker) |
| `QDRANT_HOST` | `lakeflow-qdrant` (Docker) or `localhost` (local) |
| `API_BASE_URL` | `http://lakeflow-backend:8011` (Docker) or `http://localhost:8011` (local) |
| `LAKEFLOW_MODE` | `DEV` = show Pipeline Runner; omit = hide (production) |
| `LLM_BASE_URL` | In Docker Compose / Portainer stack, defaults to `http://ollama:11434` (service `ollama`). Override for host Ollama or a proxy. |
| `EMBED_MODEL` | Default `qwen3-embedding:8b` |

---

## Project structure

```
LakeFlow/
├── backend/           # FastAPI + pipelines (Python)
│   └── src/lakeflow/
├── frontend/streamlit/# Streamlit control UI
├── website/           # Next.js docs → lake-flow.vercel.app
├── docker-compose.yml
├── env.example        # Env template (copy to .env)
└── portainer-stack.yml
```

---

## Development (without Docker)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install torch && pip install -r requirements.txt && pip install -e .
# .env in repo root with LAKE_ROOT, QDRANT_HOST, API_BASE_URL
python -m uvicorn lakeflow.main:app --reload --port 8011
```

Qdrant: `docker compose up -d qdrant`. Frontend: `streamlit run frontend/streamlit/app.py`.

---

## API overview

- `GET /health` — Health check
- `POST /auth/login` — Demo auth (`admin` / `admin123`)
- `POST /search/embed` — `{"text":"..."}` → vector
- `POST /search/semantic` — `{"query":"...", "top_k":5}`

See [backend/docs/API_EMBED.md](backend/docs/API_EMBED.md) and [lake-flow.vercel.app/docs](https://lake-flow.vercel.app/docs).

---

## CI / CD / Deploy

- **CI** (`ci.yml`): Lint (Ruff), Docker build on push/PR
- **CD** (`cd.yml`): On release tag → push images to GitHub Container Registry
- **Docker Hub** (`push-dockerhub.yml`): Push `lakeflow-backend`, `lakeflow-frontend` — needs `DOCKERHUB_USER`, `DOCKERHUB_TOKEN`
- **Deploy** (`deploy.yml`): SSH to server, `git pull`, `docker compose` on push to `main`

**Portainer:** Use `portainer-stack.yml` with pre-pushed images (no build). See deployment section in [docs](https://lake-flow.vercel.app/docs/deployment).

---

## Links

| Resource | URL |
|----------|-----|
| Website & Docs | [lake-flow.vercel.app](https://lake-flow.vercel.app) |
| PyPI | [lake-flow-pipeline](https://pypi.org/project/lake-flow-pipeline/) |

---

## Contributing

Issues, PRs, and doc improvements welcome.
