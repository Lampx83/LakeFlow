# LakeFlow

**Data Lake pipelines for Vector DB & AI.** Ingest raw documents, run staged pipelines, and produce embeddings + semantic search—ready for RAG, LLM, and analytics.

**Website:** [https://lake-flow.vercel.app/](https://lake-flow.vercel.app/) · **PyPI:** [lake-flow-pipeline](https://pypi.org/project/lake-flow-pipeline/) (e.g. [0.1.0](https://pypi.org/project/lake-flow-pipeline/0.1.0/))

[![CI](https://github.com/Lampx83/EDUAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Lampx83/EDUAI/actions/workflows/ci.yml)

---

## Quick install (one command)

Like `create-react-app` — scaffold a new LakeFlow project with one command:

```bash
pipx run lake-flow-pipeline init
```

Or specify a folder name:

```bash
pipx run lake-flow-pipeline init my-data-lake
```

You can also use `pip`:

```bash
pip install lake-flow-pipeline
lakeflow init my-data-lake
```

The CLI downloads the latest LakeFlow from GitHub, extracts it, and optionally runs Docker Compose. When done, open **http://localhost:8011** (API) and **http://localhost:8012** (Streamlit UI).

**Developer?** To contribute or customize the source, clone from GitHub and use editable install — see [CONTRIBUTING.md](CONTRIBUTING.md).

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

**Docker build (server without GPU):** Default backend image uses **PyTorch CPU-only** (no CUDA/nvidia-* ~2GB), so builds are fast. Requires `DOCKER_BUILDKIT=1` (GitHub Actions and deploy script already set it). Local build: `DOCKER_BUILDKIT=1 docker compose up --build`.  
**Mac M1 dev with GPU (Metal/MPS):** The Docker container runs Linux so Metal is not available. To use the GPU on MacBook M1, run the backend **with a venv on macOS** (see Development below): `pip install torch` then `pip install -r requirements.txt` → PyTorch will use MPS.

---

## Project structure

```
LakeFlow/
├── lake-flow/         # Package PyPI: lake-flow-pipeline (backend, CLI, API)
│   ├── pyproject.toml
│   ├── src/lakeflow/
│   └── docs/
├── lake-flow-ui/      # Package PyPI: lakeflow-ui (Streamlit control UI)
│   ├── pyproject.toml
│   ├── app.py, pages/, config/, ...
├── website/           # Landing page (Next.js, deploy to Vercel)
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
| `LLM_BASE_URL` | URL for Ollama/LLM for Q&A and **Admission agent** (e.g. `https://research.neu.edu.vn/ollama`). **The machine running LakeFlow must be able to reach this URL.** If you get "No route to host" when using Admission chat → use a local Ollama (e.g. `http://host:11434`). |
| `LLM_MODEL` | Model name (default `qwen3:8b`) |

See `.env.example` for a full template.

---

## Development (without Docker)

1. **Backend** (from repo root). **Mac M1:** install `torch` first to use GPU Metal (MPS), then install requirements.
   ```bash
   cd lake-flow
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   # Mac M1: install torch first → PyTorch uses GPU Metal (MPS)
   pip install torch
   pip install -r requirements.txt && pip install -e .
   # Ensure .env is in repo root with LAKEFLOW_DATA_BASE_PATH, QDRANT_HOST, API_BASE_URL
   python -m uvicorn lakeflow.main:app --reload --port 8011
   ```
2. **Qdrant** (if needed): `docker compose up -d qdrant`
3. **Frontend**: From repo root, load `.env` then run `lakeflow-ui` (after `pip install lake-flow-pipeline`) or `streamlit run lake-flow-ui/app.py --server.port=8012`.

Pipeline Runner in the UI is only shown when `LAKEFLOW_MODE=DEV`.

---

## API overview

- **Health:** `GET /health`
- **Auth (demo):** `POST /auth/login` (e.g. `admin` / `admin123`)
- **Embed:** `POST /search/embed` — body `{"text": "..."}` → returns `vector` / `embedding` and `dim`
- **Semantic search:** `POST /search/semantic` — body `{"query": "...", "top_k": 5}` (optional `qdrant_url`, `collection_name`)

See [lake-flow/README.md](lake-flow/README.md) and [lake-flow/docs/API_EMBED.md](lake-flow/docs/API_EMBED.md) for details.

---

## CI / CD

- **CI** (`.github/workflows/ci.yml`): On push/PR to `main` or `develop` — lint (Ruff) and Docker build for backend and frontend.
- **CD** (`.github/workflows/cd.yml`): On release (tag) — build and push images to GitHub Container Registry.
- **PyPI** (`.github/workflows/publish-pypi.yml`): On GitHub Release — publish package `lake-flow-pipeline` from the `lake-flow/` directory. See [docs/PUBLISH-PYPI.md](docs/PUBLISH-PYPI.md). Frontend is packaged separately: `lake-flow-ui/` (package `lakeflow-ui`).

Do not commit `.env`; use `.env.example` as reference.

---

## Deployment

### Running manually on the server

- Run on VPS, on-prem, or cloud (AWS, GCP, Azure).
- On the server: configure `.env` then run `docker compose up -d` (or use the deploy override: `docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build`).

### Automatic deploy on every push to `main`

The `.github/workflows/deploy.yml` workflow will SSH into the Ubuntu server, `git pull`, and run `docker compose` on every push to the `main` branch.

#### Step 1 – On the Ubuntu server (one-time setup)

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
   Log out and back in (or run `newgrp docker`) then verify: `docker compose version`.

2. **Clone the repo** (use the user you will use for SSH deploy, e.g. `ubuntu` or `deploy`)
   ```bash
   cd ~
   git clone https://github.com/Lampx83/lakeflow.git
   cd lake-flow
   ```

3. **Create `.env` file** (do not commit this file)
   ```bash
   cp .env.example .env
   nano .env
   ```
   Set at least: `LAKEFLOW_DATA_BASE_PATH=/data`, `QDRANT_HOST=lakeflow-qdrant`, `API_BASE_URL=http://lakeflow-backend:8011` (frontend in Docker calls backend by service name; do not use the server IP here).

4. **SSH key for GitHub Actions to push code**
   - On the server, create a key (if you don't have one): `ssh-keygen -t ed25519 -C "deploy" -f ~/.ssh/deploy_lakeflow -N ""`
   - Add the public key to `~/.ssh/authorized_keys`: `cat ~/.ssh/deploy_lakeflow.pub >> ~/.ssh/authorized_keys`
   - Get the **private key contents** to paste into a GitHub Secret: `cat ~/.ssh/deploy_lakeflow` (copy everything including BEGIN/END lines).

#### Step 2 – In the GitHub repo

Go to **Settings → Secrets and variables → Actions**, add **Actions secrets**:

| Secret | Required | Description |
|--------|----------|-------------|
| `DEPLOY_HOST` | Yes | Server IP or hostname (e.g. `123.45.67.89` or `myserver.com`) |
| `DEPLOY_USER` | Yes | SSH user (e.g. `ubuntu`) |
| `SSH_PRIVATE_KEY` | Yes | Full contents of the private key file (deploy_lakeflow) |
| `DEPLOY_REPO_DIR` | No | Directory containing the repo on the server; default `~/lakeflow` |
| `DEPLOY_SSH_PORT` | No | SSH port; default `22`. **If the server uses a different port (e.g. 8901), you must add this secret.** |
| `OPENAI_API_KEY` | No | Q&A defaults to Ollama (Research). If set, OpenAI is used for Q&A and the workflow writes it to `.env` on the server. |

After saving the secrets, every time you **push to `main`**, the **Deploy** workflow will run: SSH into the server → `cd <DEPLOY_REPO_DIR>` → `git pull origin main` → `docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build`.

- **Note:** The server must have Git configured (if you cloned via HTTPS, `git pull` does not need a key; if via SSH, the server needs a deploy key or use HTTPS).
- **Data:** Deploy uses a bind mount **`/datalake/research`** on the server as the data lake. Create that directory on the server (e.g. `sudo mkdir -p /datalake/research && sudo chown $USER:$USER /datalake/research`). For a team share, mount it at `/datalake/research`.
- **Mount error "SynologyDrive" / "no such file or directory":** If an old volume still points to a Mac path, on the server run **once** then push again:
  ```bash
  cd ~/lakeflow
  docker compose -f docker-compose.yml -f docker-compose.deploy.yml down -v
  ```
  The next deploy will create a new volume attached to `/datalake/research`. Old data in the volume is removed when you run `down -v`.
- **Login shows "Connection refused" (lakeflow-backend:8011):** The frontend only starts after the backend is healthy. If it still fails: (1) Check that `.env` on the server has `API_BASE_URL=http://lakeflow-backend:8011`; (2) Check backend logs: `docker logs lakeflow-backend` (if the backend crashes it won't serve /health).

---

## Contributing

Contributions are welcome: issues, pull requests, and documentation improvements. Please open an issue first for large changes.

---

## License

See the [LICENSE](LICENSE) file in this repository (if present). Otherwise, use and modification are at your own responsibility; consider adding a license before public use.
