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

**Docker build (server không GPU):** Image backend mặc định dùng **PyTorch CPU-only** (không kéo CUDA/nvidia-* ~2GB), build nhanh. Cần `DOCKER_BUILDKIT=1` (GitHub Actions và deploy script đã set). Build local: `DOCKER_BUILDKIT=1 docker compose up --build`.  
**Mac M1 dev dùng GPU (Metal/MPS):** Trong Docker container chạy Linux nên không dùng được Metal. Để tận dụng GPU trên MacBook M1, chạy backend **bằng venv trên macOS** (xem mục Development bên dưới): `pip install torch` rồi `pip install -r requirements.txt` → PyTorch sẽ dùng MPS.

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
| `LLM_BASE_URL` | URL Ollama/LLM cho Q&A và **Admission agent** (vd. `https://research.neu.edu.vn/ollama`). **Máy chạy LakeFlow phải kết nối được tới URL này.** Nếu lỗi "No route to host" khi chat Admission → dùng Ollama nội bộ (vd. `http://host:11434`). |
| `LLM_MODEL` | Tên model (mặc định `qwen3:8b`) |

See `.env.example` for a full template.

---

## Development (without Docker)

1. **Backend** (from repo root). **Mac M1:** cài `torch` trước để dùng GPU Metal (MPS), rồi mới cài requirements.
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   # Mac M1: cài torch trước → PyTorch dùng GPU Metal (MPS)
   pip install torch
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

### Chạy thủ công trên server

- Chạy trên VPS, on-prem hoặc cloud (AWS, GCP, Azure).
- Trên server: cấu hình `.env` rồi chạy `docker compose up -d` (hoặc dùng override deploy: `docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build`).

### Deploy tự động mỗi khi push lên `main`

Workflow `.github/workflows/deploy.yml` sẽ SSH vào server Ubuntu, `git pull` và chạy `docker compose` mỗi khi có push lên nhánh `main`.

#### Bước 1 – Trên server Ubuntu (chỉ làm một lần)

1. **Cài Docker và Docker Compose**
   ```bash
   sudo apt-get update && sudo apt-get install -y ca-certificates curl
   sudo install -m 0755 -d /etc/apt/keyrings
   sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   sudo chmod a+r /etc/apt/keyrings/docker.asc
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo usermod -aG docker $USER
   ```
   Đăng xuất/đăng nhập lại (hoặc `newgrp docker`) rồi kiểm tra: `docker compose version`.

2. **Clone repo** (dùng user sẽ dùng để SSH deploy, ví dụ `ubuntu` hoặc `deploy`)
   ```bash
   cd ~
   git clone https://github.com/Lampx83/lakeflow.git
   cd lakeflow
   ```

3. **Tạo file `.env`** (không commit file này)
   ```bash
   cp .env.example .env
   nano .env
   ```
   Điền ít nhất: `LAKEFLOW_DATA_BASE_PATH=/data`, `QDRANT_HOST=lakeflow-qdrant`, `API_BASE_URL=http://lakeflow-backend:8011` (frontend trong Docker gọi backend qua tên service; không dùng IP server ở đây).

4. **SSH key để GitHub Actions đẩy code**
   - Trên server tạo key (nếu chưa có): `ssh-keygen -t ed25519 -C "deploy" -f ~/.ssh/deploy_lakeflow -N ""`
   - Thêm public key vào `~/.ssh/authorized_keys`: `cat ~/.ssh/deploy_lakeflow.pub >> ~/.ssh/authorized_keys`
   - Lấy **nội dung private key** để dán vào GitHub Secret: `cat ~/.ssh/deploy_lakeflow` (copy toàn bộ kể cả dòng BEGIN/END).

#### Bước 2 – Trong GitHub repo

Vào **Settings → Secrets and variables → Actions**, thêm **Actions secrets**:

| Secret | Bắt buộc | Mô tả |
|--------|----------|--------|
| `DEPLOY_HOST` | Có | IP hoặc hostname server (vd. `123.45.67.89` hoặc `myserver.com`) |
| `DEPLOY_USER` | Có | User SSH (vd. `ubuntu`) |
| `SSH_PRIVATE_KEY` | Có | Toàn bộ nội dung file private key (deploy_lakeflow) |
| `DEPLOY_REPO_DIR` | Không | Thư mục chứa repo trên server; mặc định `~/lakeflow` |
| `DEPLOY_SSH_PORT` | Không | Cổng SSH; mặc định `22`. **Nếu server dùng cổng khác (vd. 8901) thì bắt buộc thêm secret này.** |
| `OPENAI_API_KEY` | Không | Q&A mặc định dùng Ollama (Research). Nếu khai báo, dùng OpenAI cho Q&A và workflow ghi vào `.env` trên server. |

Sau khi lưu secrets, mỗi lần bạn **push lên `main`**, workflow **Deploy** sẽ chạy: SSH vào server → `cd <DEPLOY_REPO_DIR>` → `git pull origin main` → `docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build`.

- **Lưu ý:** Trên server cần cấu hình Git (nếu clone bằng HTTPS thì `git pull` không cần key; nếu clone bằng SSH thì server cần có deploy key hoặc dùng HTTPS).
- **Data:** Deploy dùng bind mount **`/datalake/research`** trên server làm data lake. Trên server cần tạo sẵn thư mục (vd. `sudo mkdir -p /datalake/research && sudo chown $USER:$USER /datalake/research`). Nếu dùng team share, mount nó tại `/datalake/research`.
- **Lỗi mount "SynologyDrive" / "no such file or directory":** Nếu volume cũ vẫn trỏ path Mac, trên server chạy **một lần** rồi push lại:
  ```bash
  cd ~/lakeflow
  docker compose -f docker-compose.yml -f docker-compose.deploy.yml down -v
  ```
  Lần deploy tiếp theo sẽ tạo volume mới gắn với `/datalake/research`. Dữ liệu cũ trong volume bị xóa khi `down -v`.
- **Login báo "Connection refused" (lakeflow-backend:8011):** Frontend chỉ start sau khi backend healthy. Nếu vẫn lỗi: (1) Kiểm tra `.env` trên server có `API_BASE_URL=http://lakeflow-backend:8011`; (2) Xem log backend: `docker logs lakeflow-backend` (backend crash sẽ không lên được /health).

---

## Contributing

Contributions are welcome: issues, pull requests, and documentation improvements. Please open an issue first for large changes.

---

## License

See the [LICENSE](LICENSE) file in this repository (if present). Otherwise, use and modification are at your own responsibility; consider adding a license before public use.
