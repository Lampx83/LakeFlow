import { DocPage } from "@/components/docs/DocPage";

const URL_BACKEND = "http://localhost:8011";
const URL_FRONTEND = "http://localhost:8012";
const URL_QDRANT = "http://localhost:8013";

export default function GettingStartedPage() {
  return (
    <DocPage
      title="Getting Started"
      nextHref="/docs/backend-api"
      nextLabel="Backend API"
    >
      <h2>System requirements</h2>
      <ul>
        <li><strong>Docker</strong> ≥ 20.x and <strong>Docker Compose</strong> ≥ 2.x (for Docker install)</li>
        <li><strong>Python 3.10+</strong> (for local dev without Docker)</li>
        <li>Disk space: backend image ~2GB (PyTorch CPU), Qdrant ~500MB</li>
      </ul>

      <h2>Quick install (Docker)</h2>
      <p>Run Backend, Frontend and Qdrant with Docker Compose:</p>
      <ol className="list-decimal space-y-2 pl-5 mt-2">
        <li><strong>Clone and prepare env:</strong></li>
      </ol>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`git clone https://github.com/Lampx83/LakeFlow.git LakeFlow
cd LakeFlow
cp env.example .env   # or cp .env.example .env`}
      </pre>
      <ol className="list-decimal space-y-2 pl-5 mt-2" start={2}>
        <li><strong>Required:</strong> Edit <code>.env</code> — set <code>HOST_LAKE_PATH</code> to the absolute path of the Data Lake directory. Examples:
          <ul className="mt-1 list-disc pl-5">
            <li>macOS: <code>HOST_LAKE_PATH=/Users/you/lakeflow_data</code></li>
            <li>Linux: <code>HOST_LAKE_PATH=/datalake/research</code></li>
          </ul>
          Directory must exist before running.
        </li>
        <li>Create directory if needed: <code>mkdir -p $HOST_LAKE_PATH</code></li>
        <li>Create zones: <code>mkdir -p $HOST_LAKE_PATH/000_inbox $HOST_LAKE_PATH/100_raw $HOST_LAKE_PATH/200_staging $HOST_LAKE_PATH/300_processed $HOST_LAKE_PATH/400_embeddings $HOST_LAKE_PATH/500_catalog</code></li>
        <li>Run: <code>docker compose up --build</code> (or <code>-d</code> for background)</li>
      </ol>
      <p className="mt-2 text-amber-200/90"><strong>Note:</strong> Docker volume uses <code>device: $HOST_LAKE_PATH</code>. Empty variable or non-existent path will cause compose to fail.</p>
      <p className="mt-3">
        After successful startup, services are available at:
      </p>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr><th>Service</th><th>URL</th><th>Notes</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>Backend API</td>
            <td><a href={URL_BACKEND} target="_blank" rel="noopener noreferrer" className="text-brand-400">{URL_BACKEND}</a></td>
            <td>Base URL for API calls</td>
          </tr>
          <tr>
            <td>Swagger UI</td>
            <td><a href={`${URL_BACKEND}/docs`} target="_blank" rel="noopener noreferrer" className="text-brand-400">{URL_BACKEND}/docs</a></td>
            <td>Interactive API docs</td>
          </tr>
          <tr>
            <td>Streamlit UI</td>
            <td><a href={URL_FRONTEND} target="_blank" rel="noopener noreferrer" className="text-brand-400">{URL_FRONTEND}</a></td>
            <td>Login: <code>admin</code> / <code>admin123</code></td>
          </tr>
          <tr>
            <td>Qdrant</td>
            <td>{URL_QDRANT}</td>
            <td>Vector DB (port 6333 in container mapped to 8013)</td>
          </tr>
        </tbody>
      </table>

      <h2>Project structure</h2>
      <pre className="code-block mt-3 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`LakeFlow/
├── backend/                   # FastAPI + pipeline scripts (Python)
│   ├── src/lakeflow/          # Main package
│   │   ├── api/               # Routers: auth, search, pipeline, inbox, qdrant, ...
│   │   ├── scripts/           # step0_inbox, step1_raw, step2_staging, step3, step4
│   │   └── ...
│   └── requirements.txt
├── frontend/streamlit/        # Streamlit control UI
│   ├── app.py                 # Entry point
│   ├── pages/                 # Dashboard, Pipeline Runner, Semantic Search, ...
│   └── services/              # api_client, pipeline_service, ...
├── website/                   # Docs site (Next.js)
├── docker-compose.yml        # Docker config
├── env.example               # Env var template
└── README.md`}
      </pre>

      <h2>Local development (without Docker)</h2>
      <p>Run backend and frontend directly on your machine for faster debugging. Requires Python 3.10+.</p>
      <ol className="list-decimal space-y-2 pl-5 mt-2">
        <li><strong>Qdrant:</strong> <code>docker compose up -d qdrant</code></li>
        <li><strong>Backend:</strong>
          <pre className="mt-1 overflow-x-auto rounded border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs text-brand-400">{`cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install torch           # Mac M1: install first for Metal (MPS)
pip install -r requirements.txt && pip install -e .
uvicorn lakeflow.main:app --reload --port 8011`}</pre>
        </li>
        <li><strong>Frontend:</strong> From repo root:
          <pre className="mt-1 overflow-x-auto rounded border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs text-brand-400">{`python frontend/streamlit/dev_with_reload.py
# or: streamlit run frontend/streamlit/app.py`}</pre>
        </li>
      </ol>
      <p className="mt-2">
        <code>.env</code> in repo root needs: <code>LAKE_ROOT</code>, <code>QDRANT_HOST=localhost</code>, <code>API_BASE_URL=http://localhost:8011</code>. <code>dev_with_reload.py</code> auto-loads <code>.env</code> from repo root.
      </p>

      <h2>First run workflow</h2>
      <ol className="list-decimal space-y-2 pl-5">
        <li><strong>Create zones</strong> (if needed): <code>mkdir -p $HOST_LAKE_PATH/000_inbox $HOST_LAKE_PATH/100_raw $HOST_LAKE_PATH/200_staging $HOST_LAKE_PATH/300_processed $HOST_LAKE_PATH/400_embeddings $HOST_LAKE_PATH/500_catalog</code></li>
        <li><strong>Add files to inbox:</strong> Copy PDF/Word/Excel to <code>000_inbox/&lt;domain&gt;/</code> (e.g. <code>000_inbox/regulations/doc.pdf</code>) or call <code>POST /inbox/upload</code></li>
        <li><strong>Run pipeline:</strong> Via Streamlit (Pipeline Runner) or API: <code>POST /pipeline/run/step0</code> → step1 → step2 → step3 → step4</li>
        <li><strong>Test search:</strong> Semantic Search page in UI or <code>POST /search/semantic</code></li>
      </ol>
      <p className="mt-2 text-amber-200/90"><strong>Note:</strong> Step3 (embedding) and Semantic Search need Ollama (<code>LLM_BASE_URL</code>). Run <code>ollama pull qwen3-embedding:8b</code> (or your chosen model) first.</p>

      <h2>Mac M1 / Metal (MPS)</h2>
      <p>
        Docker runs Linux so Metal/MPS is not available in container. To use GPU on Mac M1, run backend via venv on macOS: <code>pip install torch</code> first then <code>pip install -r requirements.txt</code>. PyTorch will use MPS.
      </p>

      <h2>Build on server without GPU</h2>
      <p>Backend image defaults to PyTorch CPU-only (~2GB). Requires <code>DOCKER_BUILDKIT=1</code> when building: <code>DOCKER_BUILDKIT=1 docker compose up --build</code></p>

      <h2>Troubleshooting</h2>
      <ul>
        <li><strong>Compose error:</strong> Ensure <code>HOST_LAKE_PATH</code> exists and is an absolute path.</li>
        <li><strong>Frontend &quot;Connection refused&quot;:</strong> Backend must run first; check <code>API_BASE_URL</code>.</li>
        <li><strong>Search returns empty:</strong> Have you run step3 + step4? Does collection have data? Check <code>EMBED_MODEL</code> matches model used in step3.</li>
      </ul>
    </DocPage>
  );
}
