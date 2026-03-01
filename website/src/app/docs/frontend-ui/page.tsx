import { DocPage } from "@/components/docs/DocPage";

export default function FrontendUiPage() {
  return (
    <DocPage
      title="Frontend (Streamlit)"
      prevHref="/docs/backend-api"
      prevLabel="Backend API"
      nextHref="/docs/data-lake"
      nextLabel="Data Lake Architecture"
    >
      <p>
        LakeFlow frontend is a <strong>Streamlit</strong> control UI at <code>http://localhost:8012</code>. Connects to Backend API to run pipelines, explore Data Lake, and test Semantic Search.
      </p>

      <h2>Login</h2>
      <p>Default: <code>admin</code> / <code>admin123</code>. JWT token is stored in session and sent with every API request.</p>
      <p className="mt-1">Pages requiring login: Q&amp;A with AI, System Settings (some operations). Other pages can be used once backend is ready.</p>

      <h2>Pages overview</h2>
      <div className="space-y-6 mt-4">
        <div>
          <h3 className="text-lg font-semibold">Dashboard</h3>
          <p>Pipeline status overview, run history. Quick view of file count per zone, recent pipelines.</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">Data Lake Explorer</h3>
          <p>Browse zone directory tree: inbox → raw → staging → processed → embeddings → catalog. Select zone and path to view files; preview JSON content (validation.json, chunks.json).</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">Pipeline Runner</h3>
          <p><em>Only shown when <code>LAKEFLOW_MODE=DEV</code>.</em> Manually run step0→step4. Options:</p>
          <ul className="list-disc pl-5 mt-1">
            <li>Select folder (domain or file_hash) — run on subset only</li>
            <li>Enable Force rerun — run again even if already processed</li>
            <li>Step3: choose embed model from dropdown (from <code>EMBED_MODEL_OPTIONS</code>)</li>
            <li>Step4: choose collection_name, qdrant_url</li>
          </ul>
          <p className="mt-1">Results show returncode, stdout, stderr.</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">SQLite Viewer</h3>
          <p>View SQLite databases in Data Lake (e.g. catalog, app DB). Select .db file, view tables and query.</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">Qdrant Inspector</h3>
          <p>List collections, view points in a collection. Supports custom Qdrant URL (multi-Qdrant). Useful to verify vectors after step4.</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">Semantic Search</h3>
          <p>Enter natural language question, get results with score. Can select collection, Qdrant URL, top_k. Use to test search before integrating API.</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">Q&amp;A with AI</h3>
          <p>RAG Q&amp;A: ask question → semantic search finds context → LLM (Ollama/OpenAI) answers. Login required. Displays contexts and answer.</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">System Settings</h3>
          <p>Full configuration: Connection status (Backend, Qdrant), runtime config table (Data Lake path, Qdrant URL, Embed/LLM model, OpenAI key set), zone status (file counts), create missing zones button, Data Lake path config. Does not display secrets (API key).</p>
        </div>
      </div>

      <h2>Multi–Qdrant</h2>
      <p>Semantic Search and Qdrant Inspector allow entering custom Qdrant URL and collection. Use when testing multiple vector stores or environments.</p>

      <h2>Frontend code structure</h2>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`frontend/streamlit/
├── app.py                  # Entry, sidebar, routing
├── pages/                  # Each file = one page (Streamlit auto-detect)
│   ├── pipeline_dashboard.py
│   ├── data_lake_explorer.py
│   ├── pipeline_runner.py
│   ├── sqlite_viewer.py
│   ├── qdrant_inspector.py
│   ├── semantic_search.py
│   ├── qa.py               # Q&A with AI
│   ├── system_settings.py
│   ├── admin.py
│   └── login.py
├── state/
│   ├── session.py         # Session init
│   └── token_store.py     # Auth token storage
└── services/
    ├── api_client.py      # HTTP client for backend
    ├── pipeline_service.py  # Calls /pipeline/run/*
    └── qdrant_service.py  # Qdrant API calls`}
      </pre>

      <h2>Run locally</h2>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`# From repo root
# dev_with_reload auto-loads .env from repo root
python frontend/streamlit/dev_with_reload.py

# Or run Streamlit directly (need .env or export vars)
streamlit run frontend/streamlit/app.py`}
      </pre>
      <p className="mt-2">
        When running backend locally: set <code>API_BASE_URL=http://localhost:8011</code> in <code>.env</code>. Frontend auto-resolves <code>lakeflow-backend</code> → <code>localhost</code> when hostname does not resolve (in Docker, uses service name).
      </p>

      <h2>Troubleshooting</h2>
      <ul>
        <li><strong>Connection refused:</strong> Check backend is running, <code>API_BASE_URL</code> is correct. In Docker, frontend calls <code>lakeflow-backend:8011</code>.</li>
        <li><strong>Pipeline Runner not showing:</strong> Set <code>LAKEFLOW_MODE=DEV</code> in <code>.env</code>.</li>
        <li><strong>Q&amp;A 401 error:</strong> Log in again; token may have expired.</li>
      </ul>
    </DocPage>
  );
}
