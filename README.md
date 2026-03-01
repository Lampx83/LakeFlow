# LakeFlow

**Data Lake pipelines for Vector DB & AI.** Ingest raw documents, run staged pipelines, and produce embeddings + semantic search—ready for RAG, LLM, and analytics.

**Website:** [https://lake-flow.vercel.app](https://lake-flow.vercel.app) — full documentation, getting started, API reference, and deployment guides.

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
# Edit .env: set LAKE_ROOT to a directory that will hold the data lake (or leave /data for Docker volume)
docker compose up --build
```

- **Backend API:** http://localhost:8011  
- **API docs:** http://localhost:8011/docs  
- **Streamlit UI:** http://localhost:8012 (login: `admin` / `admin123`)

Data lake root is the `lakeflow_data` volume (or path you set). Create zones manually if needed: `000_inbox`, `100_raw`, `200_staging`, `300_processed`, `400_embeddings`, `500_catalog`.

**Docker build (server without GPU):** Backend image defaults to **PyTorch CPU-only** (no CUDA/nvidia-* ~2GB), fast build. Requires `DOCKER_BUILDKIT=1` (GitHub Actions and deploy script already set). Local build: `DOCKER_BUILDKIT=1 docker compose up --build`.  
**Mac M1 dev with GPU (Metal/MPS):** Docker container runs Linux so Metal is not available. To use GPU on MacBook M1, run backend **via venv on macOS** (see Development section below): `pip install torch` then `pip install -r requirements.txt` → PyTorch will use MPS.

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
├── website/           # Next.js docs site → https://lake-flow.vercel.app
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Description |
|----------|-------------|
| `LAKE_ROOT` | Root path for the data lake (e.g. `/data` in Docker, or a host path) |
| `LAKEFLOW_MODE` | `DEV` = show Pipeline Runner in UI; omit or other = hide |
| `QDRANT_HOST` | Qdrant host (e.g. `lakeflow-qdrant` in Docker, `localhost` when running Qdrant alone) |
| `API_BASE_URL` | Backend URL (e.g. `http://lakeflow-backend:8011` in Docker, `http://localhost:8011` for local dev) |
| `LLM_BASE_URL` | URL for Ollama/LLM for Q&A and **Admission agent**. **The machine running LakeFlow must be able to connect to this URL.** If "No route to host" when chatting Admission → use internal Ollama (e.g. `http://host:11434`). |
| `LLM_MODEL` | Model name (default `qwen3:8b`) |

See `.env.example` for a full template.

---

## Development (without Docker)

1. **Backend** (from repo root). **Mac M1:** install `torch` first for GPU Metal (MPS), then install requirements.
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   # Mac M1: install torch first → PyTorch uses GPU Metal (MPS)
   pip install torch
   pip install -r requirements.txt && pip install -e .
   # Ensure .env is in repo root with LAKE_ROOT, QDRANT_HOST, API_BASE_URL
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

See [backend/README.md](backend/README.md) and [backend/docs/API_EMBED.md](backend/docs/API_EMBED.md) for details. Full docs: [lake-flow.vercel.app/docs](https://lake-flow.vercel.app/docs).

---

## CI / CD

- **CI** (`.github/workflows/ci.yml`): On push/PR to `main` or `develop` — lint (Ruff) and Docker build for backend and frontend.
- **CD** (`.github/workflows/cd.yml`): On release (tag) — build and push images to GitHub Container Registry.
- **Push to Docker Hub** (`.github/workflows/push-dockerhub.yml`): On push to `main` (when `backend/` or `frontend/` changes) — build and push `lakeflow-backend:latest`, `lakeflow-frontend:latest` to Docker Hub. Requires secrets: `DOCKERHUB_USER`, `DOCKERHUB_TOKEN`.
- **PyPI** (`.github/workflows/publish-pypi.yml`): On GitHub Release — publish package `lake-flow-pipeline` from the `backend/` directory. See [docs/PUBLISH-PYPI.md](docs/PUBLISH-PYPI.md). Frontend package `lakeflow-ui` from `frontend/streamlit/`.

Do not commit `.env`; use `.env.example` as reference.

---

## Deployment

### Portainer Stack

**Portainer does not support `build`** in stack → use **pre-pushed images** on Docker Hub.

1. **Build and push** (run on machine with Docker):
   ```bash
   cd LakeFlow
   export DOCKERHUB_USER=your-username
   docker build -t $DOCKERHUB_USER/lakeflow-backend:latest ./backend
   docker build -t $DOCKERHUB_USER/lakeflow-frontend:latest ./frontend/streamlit
   docker push $DOCKERHUB_USER/lakeflow-backend:latest
   docker push $DOCKERHUB_USER/lakeflow-frontend:latest
   ```
2. **Portainer:** Stacks → Add stack → Web editor → paste contents of `portainer-stack.yml`.
3. **Env vars** in Portainer: `DOCKERHUB_USER`, and required vars from `.env.example` (e.g. `LAKE_ROOT`, `QDRANT_HOST`).

See `portainer-stack.yml` in the LakeFlow directory.

### Manual run on server

- Run on VPS, on-prem or cloud (AWS, GCP, Azure).
- On server: configure `.env` then run `docker compose up -d` (or use deploy override: `docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build`).

### Auto deploy on push to `main`

Workflow `.github/workflows/deploy.yml` will SSH into Ubuntu server, `git pull` and run `docker compose` on each push to `main` branch.

#### Step 1 – On Ubuntu server (one-time setup)

1. **Install Docker and Docker Compose**
   ```bash
   sudo apt-get update && sudo apt-get install -y ca-certificates curl
   sudo install -m 0755 -d /etc/apt/keyrings
   sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   sudo chmod a+r /etc/apt/keyrings/docker.asc
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo usermod -aG docker $USER
   ```
   Log out and back in (or `newgrp docker`) then verify: `docker compose version`.

2. **Clone repo** (use user for SSH deploy, e.g. `ubuntu` or `deploy`)
   ```bash
   cd ~
   git clone https://github.com/Lampx83/lakeflow.git
   cd lakeflow
   ```

3. **Create `.env` file** (do not commit this file)
   ```bash
   cp .env.example .env
   nano .env
   ```
   Fill at least: `LAKE_ROOT=/data`, `QDRANT_HOST=lakeflow-qdrant`, `API_BASE_URL=http://lakeflow-backend:8011` (frontend in Docker calls backend via service name; do not use server IP here).

4. **SSH key for GitHub Actions to push code**
   - On server create key (if not exists): `ssh-keygen -t ed25519 -C "deploy" -f ~/.ssh/deploy_lakeflow -N ""`
   - Add public key to `~/.ssh/authorized_keys`: `cat ~/.ssh/deploy_lakeflow.pub >> ~/.ssh/authorized_keys`
   - Get **private key content** to paste into GitHub Secret: `cat ~/.ssh/deploy_lakeflow` (copy entire content including BEGIN/END lines).

#### Step 2 – In GitHub repo

Go to **Settings → Secrets and variables → Actions**, add **Actions secrets**:

| Secret | Required | Description |
|--------|----------|-------------|
| `DEPLOY_HOST` | Yes | Server IP or hostname (e.g. `123.45.67.89` or `myserver.com`) |
| `DEPLOY_USER` | Yes | SSH user (e.g. `ubuntu`) |
| `SSH_PRIVATE_KEY` | Yes | Full content of private key file (deploy_lakeflow) |
| `DEPLOY_REPO_DIR` | No | Repo directory on server; default `~/lakeflow` |
| `DEPLOY_SSH_PORT` | No | SSH port; default `22`. **If server uses different port (e.g. 8901) this secret is required.** |
| `OPENAI_API_KEY` | No | Q&A defaults to Ollama (Research). If set, use OpenAI for Q&A and workflow writes to `.env` on server. |

After saving secrets, each time you **push to `main`**, the **Deploy** workflow will run: SSH into server → `cd <DEPLOY_REPO_DIR>` → `git pull origin main` → `docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build`.

- **Note:** Server needs Git configured (if clone via HTTPS then `git pull` needs no key; if clone via SSH then server needs deploy key or use HTTPS).
- **Data:** Deploy uses bind mount **`/datalake/research`** on server as data lake. Create directory on server (e.g. `sudo mkdir -p /datalake/research && sudo chown $USER:$USER /datalake/research`). For team share, mount it at `/datalake/research`.
- **Mount error "SynologyDrive" / "no such file or directory":** If old volume still points to Mac path, on server run **once** then push again:
  ```bash
  cd ~/lakeflow
  docker compose -f docker-compose.yml -f docker-compose.deploy.yml down -v
  ```
  Next deploy will create new volume attached to `/datalake/research`. Old data in volume is removed when `down -v`.
- **Login shows "Connection refused" (lakeflow-backend:8011):** Frontend starts only after backend is healthy. If still failing: (1) Check server `.env` has `API_BASE_URL=http://lakeflow-backend:8011`; (2) View backend log: `docker logs lakeflow-backend` (backend crash will not reach /health).

---

## Links

| Resource | URL |
|----------|-----|
| **Website & Docs** | [https://lake-flow.vercel.app](https://lake-flow.vercel.app) |
| **PyPI** | [lake-flow-pipeline](https://pypi.org/project/lake-flow-pipeline/) |

---

## Contributing

Contributions are welcome: issues, pull requests, and documentation improvements. Please open an issue first for large changes.

---

## License

See the [LICENSE](LICENSE) file in this repository (if present). Otherwise, use and modification are at your own responsibility; consider adding a license before public use.
