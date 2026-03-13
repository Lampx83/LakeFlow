import { DocPage } from "@/components/docs/DocPage";

export default function BackendApiPage() {
  return (
    <DocPage
      titleKey="docs.pages.backendApi.title"
      prevHref="/docs/getting-started"
      prevLabelKey="docs.sidebar.gettingStarted"
      nextHref="/docs/frontend-ui"
      nextLabelKey="docs.sidebar.frontendUi"
    >
      <p>
        LakeFlow backend is a <strong>FastAPI</strong> application. Base URL: <code>http://localhost:8011</code> (dev) or deployment URL.
      </p>
      <p className="mt-2">
        <strong>Interactive docs:</strong> Swagger UI <code>/docs</code>, ReDoc <code>/redoc</code>. Use Bearer token from <code>POST /auth/login</code> for auth-required endpoints.
      </p>

      <h2>Routes overview</h2>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>Endpoint</th>
            <th>Method</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>/health</code></td>
            <td>GET</td>
            <td>Health check. Response: <code>{"{status: ok}"}</code>. For liveness probe.</td>
          </tr>
          <tr>
            <td><code>/auth</code></td>
            <td>—</td>
            <td>Login (<code>POST /auth/login</code>), token, <code>GET /auth/me</code></td>
          </tr>
          <tr>
            <td><code>/search</code></td>
            <td>—</td>
            <td>Embed (<code>POST /embed</code>), semantic (<code>POST /semantic</code>), Q&amp;A (<code>POST /qa</code>)</td>
          </tr>
          <tr>
            <td><code>/pipeline</code></td>
            <td>—</td>
            <td>Run pipeline step0–step4 (<code>GET /folders/&#123;step&#125;</code>, <code>POST /run/&#123;step&#125;</code>)</td>
          </tr>
          <tr>
            <td><code>/system</code></td>
            <td>—</td>
            <td>Path Data Lake: <code>GET/POST /data-path</code></td>
          </tr>
          <tr>
            <td><code>/qdrant</code></td>
            <td>—</td>
            <td>Proxy Qdrant: collections, points, filter</td>
          </tr>
          <tr>
            <td><code>/inbox</code></td>
            <td>—</td>
            <td>Upload (<code>POST /upload</code>), <code>GET /domains</code>, <code>GET /list</code></td>
          </tr>
          <tr>
            <td><code>/admin</code></td>
            <td>—</td>
            <td>Users, delete messages</td>
          </tr>
          <tr>
            <td><code>/admission_agent/v1</code></td>
            <td>—</td>
            <td>Example agent for AI Portal. See Admission Agent section.</td>
          </tr>
        </tbody>
      </table>

      <h2>Auth</h2>
      <p>Demo mechanism: username/password hard-coded. JWT token used for protected endpoints (Q&amp;A, Admin).</p>
      <h3>POST /auth/login</h3>
      <p><strong>Request:</strong> <code>{"{ username: string, password: string }"}</code></p>
      <p><strong>Response:</strong> <code>{"{ access_token: string }"}</code> — JWT, expires in 24h</p>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`# Example: login and save token
TOKEN=$(curl -s -X POST "http://localhost:8011/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')`}
      </pre>
      <h3>GET /auth/me</h3>
      <p>Requires header <code>Authorization: Bearer &lt;token&gt;</code>. Returns <code>{"{ username: string }"}</code>.</p>
      <p className="mt-2"><strong>Endpoints requiring Bearer token:</strong> <code>POST /search/qa</code>, <code>GET /admin/users</code>, <code>DELETE /admin/users/&#123;username&#125;/messages</code>, <code>GET /admission_agent/v1/metadata</code>, <code>POST /admission_agent/v1/ask</code>, <code>GET /admission_agent/v1/data</code>.</p>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`curl -X POST "http://localhost:8011/search/qa" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer $TOKEN" \\
  -d '{"question":"What is the enrollment quota?","top_k":5}'`}
      </pre>

      <h2>Search APIs</h2>
      <p>All use <code>EMBED_MODEL</code> (Ollama). Ensure model is pulled (<code>ollama pull qwen3-embedding:8b</code>).</p>
      <h3>POST /search/embed</h3>
      <p>Convert text to vector. Same model as semantic search and step3 embedding.</p>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>Field</th>
            <th>Type</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>text</code></td>
            <td>string</td>
            <td>Text to embed (required)</td>
          </tr>
        </tbody>
      </table>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`curl -X POST "http://localhost:8011/search/embed" \\
  -H "Content-Type: application/json" \\
  -d '{"text":"University admission regulations"}'`}
      </pre>
      <p><strong>Response:</strong> <code>{"{ text, vector, embedding, dim }"}</code> — <code>vector</code> and <code>embedding</code> are the same; <code>dim</code> depends on model (e.g. qwen3-embedding:8b ≈ 1024).</p>

      <h3>POST /search/semantic</h3>
      <p>Semantic search via Qdrant. Returns chunks by cosine similarity.</p>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>Field</th>
            <th>Type</th>
            <th>Default</th>
          </tr>
        </thead>
        <tbody>
          <tr><td><code>query</code></td><td>string</td><td>—</td></tr>
          <tr><td><code>top_k</code></td><td>int</td><td>5</td></tr>
          <tr><td><code>collection_name</code></td><td>string?</td><td>lakeflow_chunks</td></tr>
          <tr><td><code>score_threshold</code></td><td>float?</td><td>—</td></tr>
          <tr><td><code>qdrant_url</code></td><td>string?</td><td>default Qdrant</td></tr>
        </tbody>
      </table>
      <p><strong>Response:</strong> <code>{"{ query, results: [{ id, score, file_hash, chunk_id, section_id, text, token_estimate, source }] }"}</code></p>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`curl -X POST "http://localhost:8011/search/semantic" \\
  -H "Content-Type: application/json" \\
  -d '{"query":"admission requirements","top_k":5,"collection_name":"lakeflow_chunks"}'`}
      </pre>

      <h3>POST /search/qa</h3>
      <p>RAG Q&amp;A: find context via semantic search, then LLM (Ollama/OpenAI) answers. <strong>Requires Bearer token.</strong></p>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>Field</th>
            <th>Type</th>
            <th>Default</th>
          </tr>
        </thead>
        <tbody>
          <tr><td><code>question</code></td><td>string</td><td>—</td></tr>
          <tr><td><code>top_k</code></td><td>int</td><td>5</td></tr>
          <tr><td><code>temperature</code></td><td>float</td><td>0.7</td></tr>
          <tr><td><code>collection_name</code></td><td>string?</td><td>—</td></tr>
          <tr><td><code>score_threshold</code></td><td>float?</td><td>—</td></tr>
          <tr><td><code>qdrant_url</code></td><td>string?</td><td>—</td></tr>
        </tbody>
      </table>
      <p><strong>Response:</strong> <code>{"{ question, answer, contexts, model_used, debug_info }"}</code>. <code>debug_info</code> contains <code>steps_completed</code>, <code>curl_embed</code>, <code>curl_search</code>, <code>curl_complete</code> for debugging.</p>

      <h2>Pipeline API</h2>
      <p>Run each pipeline step (step0→step4). Each step is a subprocess running Python script; timeout 1h.</p>
      <h3>GET /pipeline/embed-models</h3>
      <p>List of models for step3. Returns <code>{"{ models: string[], default: string }"}</code> — from <code>EMBED_MODEL_OPTIONS</code> or default list.</p>

      <h3>GET /pipeline/folders/&#123;step&#125;</h3>
      <p>List folders that can be run for the step. step0: domain in inbox; step1: file_hash; step2/3/4: domain or file_hash.</p>
      <p><strong>Response:</strong> <code>{"{ step, folders: string[] }"}</code></p>

      <h3>POST /pipeline/run/&#123;step&#125;</h3>
      <p>Run one pipeline step. Body (optional):</p>
      <ul>
        <li><code>only_folders</code> — run only on these folders (domain or file_hash)</li>
        <li><code>force_rerun</code> — run again even if already processed</li>
        <li><code>embed_model</code> — step3 only: Ollama model (e.g. <code>qwen3-embedding:8b</code>, <code>nomic-embed-text</code>)</li>
        <li><code>collection_name</code> — step4 only: Qdrant collection name (default <code>lakeflow_chunks</code>)</li>
        <li><code>qdrant_url</code> — step4 only: Qdrant URL (e.g. <code>http://host:6333</code>)</li>
      </ul>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`# Run all
curl -X POST "http://localhost:8011/pipeline/run/step0" -H "Content-Type: application/json" -d '{}'

# regulations domain only, force rerun
curl -X POST "http://localhost:8011/pipeline/run/step3" -H "Content-Type: application/json" \\
  -d '{"only_folders":["regulations"],"force_rerun":true,"embed_model":"nomic-embed-text"}'`}
      </pre>
      <p><strong>Response:</strong> <code>{"{ step, script, returncode, stdout, stderr }"}</code>. <code>returncode=0</code> means success.</p>

      <h2>System API</h2>
      <ul>
        <li><code>GET /system/health-detail</code> — Backend status + Qdrant connection. Returns <code>backend</code>, <code>qdrant_connected</code>, <code>qdrant_error</code>, <code>qdrant_url</code>.</li>
        <li><code>GET /system/config</code> — Runtime config (no secrets). For System Settings UI.</li>
        <li><code>GET /system/zones-status</code> — Per-zone status: exists, file_count. Returns <code>zones[]</code>, <code>all_zones_exist</code>.</li>
        <li><code>POST /system/create-zones</code> — Create missing zones in current path. Idempotent.</li>
        <li><code>GET /system/data-path</code> — Returns <code>{"{ data_base_path: string | null }"}</code> (current LAKE_ROOT)</li>
        <li><code>POST /system/data-path</code> — Body <code>{"{ path: string }"}</code> — Set Data Lake path. Path must exist and have all 6 zones.</li>
      </ul>

      <h2>Inbox API</h2>
      <p>Upload files to inbox and auto-run pipeline step0→step4 (background).</p>
      <h3>POST /inbox/upload</h3>
      <p><strong>Multipart form:</strong></p>
      <table className="mt-2 w-full text-sm">
        <thead><tr><th>Field</th><th>Required</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td><code>domain</code></td><td>Yes</td><td>Subfolder in 000_inbox (e.g. regulations, syllabus). Only a-z, 0-9, _, -</td></tr>
          <tr><td><code>path</code></td><td>No</td><td>Subpath within domain (e.g. folder1/folder2)</td></tr>
          <tr><td><code>files</code></td><td>Yes</td><td>File(s) to upload. Supported: .pdf, .docx, .xlsx, .xls, .pptx, .txt. Max 100 MB/file</td></tr>
          <tr><td><code>qdrant_url</code></td><td>No</td><td>Qdrant URL for step4 (default uses default Qdrant)</td></tr>
        </tbody>
      </table>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`# Upload a single file
curl -X POST "http://localhost:8011/inbox/upload" \\
  -F "domain=regulations" \\
  -F "files=@document.pdf"

# Upload multiple files to subpath
curl -X POST "http://localhost:8011/inbox/upload" \\
  -F "domain=syllabus" \\
  -F "path=2024/course_a" \\
  -F "files=@doc1.pdf" -F "files=@doc2.docx"`}
      </pre>
      <p><strong>Response:</strong> <code>{"{ uploaded: string[], errors: string[] }"}</code>. After successful upload, pipeline runs in background; step4 uses <code>collection_name = domain</code>.</p>
      <h3>GET /inbox/domains</h3>
      <p>Returns <code>{"{ domains: string[] }"}</code> — list of top-level folders in 000_inbox.</p>
      <h3>GET /inbox/list</h3>
      <p><strong>Query params:</strong> <code>domain</code> (optional), <code>path</code> (optional).</p>
      <p><strong>Response:</strong> Without domain: <code>{"{ domains[], files[], folders[] }"}</code>. With domain: <code>{"{ domain, path, folders[], files[] }"}</code> — files have <code>name</code>, <code>size</code>, <code>mtime</code>.</p>

      <h2>Admin API</h2>
      <p><strong>Requires Bearer token.</strong></p>
      <ul>
        <li><code>GET /admin/users</code> — List users and message stats (for Q&amp;A)</li>
        <li><code>DELETE /admin/users/&#123;username&#125;/messages</code> — Delete user message history</li>
      </ul>

      <h2>Admission Agent — Example for AI Portal</h2>
      <p>
        <code>/admission_agent/v1</code> is an <strong>example agent</strong> that demonstrates how to build an AI agent for <strong>AI Portal</strong> to consume.
        LakeFlow handles the data pipeline (documents → inbox → embedding → Qdrant); this agent exposes a compatible API so AI Portal can connect and use the data.
      </p>
      <p className="mt-2">
        <strong>Use case:</strong> Upload admission/enrollment documents to the Data Lake, run the pipeline into the <code>Admission</code> collection, then register this agent in AI Portal. Users can then ask questions via AI Portal; the agent uses semantic search + LLM (RAG) to answer.
      </p>
      <p className="mt-2">
        You can implement similar agents for other domains (regulations, syllabus, etc.) by replicating this pattern. API shape matches Research Agent (<code>/metadata</code>, <code>/data</code>, <code>/ask</code>).
      </p>

      <h3>Endpoints</h3>
      <ul>
        <li><code>GET /admission_agent/v1/metadata</code> — Agent metadata (name, description, capabilities). May be public; AI Portal uses this to discover the agent.</li>
        <li><code>GET /admission_agent/v1/data</code> — List of data sources from Admission collection. <strong>Requires Bearer token.</strong></li>
        <li><code>POST /admission_agent/v1/ask</code> — RAG Q&amp;A over Admission documents. Body: <code>{"{ prompt: string, session_id?: string, model_id?: string, user?: string, context?: object }"}</code>. Only <code>prompt</code> is required. <strong>Requires Bearer token.</strong></li>
      </ul>

      <h3>Requirements</h3>
      <ul>
        <li><code>LLM_BASE_URL</code> (Ollama) — for embedding and chat completion</li>
        <li>Data in Qdrant collection <code>Admission</code> — ingest documents via LakeFlow pipeline (domain → step0→step4 with <code>collection_name=Admission</code>)</li>
      </ul>

      <h3>Example: register in AI Portal</h3>
      <p>Provide AI Portal with the agent base URL (e.g. <code>http://your-backend:8011/admission_agent/v1</code>). AI Portal will call <code>/metadata</code> to display the agent, then <code>/ask</code> (with user token) for questions.</p>

      <h2>Qdrant proxy</h2>
      <p>Proxy to Qdrant REST API. Query collections and points without direct Qdrant access.</p>
      <ul>
        <li><code>GET /qdrant/collections</code> — List collections</li>
        <li><code>GET /qdrant/collections/&#123;name&#125;</code> — Collection info</li>
        <li><code>GET /qdrant/collections/&#123;name&#125;/points</code> — Get points (scroll, limit, offset)</li>
        <li><code>POST /qdrant/collections/&#123;name&#125;/filter</code> — Filter points (body: filter conditions)</li>
      </ul>
      <p>Supports <code>qdrant_url</code> to point to different Qdrant (multi-Qdrant). See Swagger for request body details.</p>

      <h2 id="python-integration">Python integration example</h2>
      <p>Use <code>requests</code> to call APIs from Python:</p>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`import requests

BASE = "http://localhost:8011"

# 1. Semantic search (no auth)
r = requests.post(f"{BASE}/search/semantic", json={
    "query": "admission regulations",
    "top_k": 5,
    "collection_name": "lakeflow_chunks"
})
results = r.json()["results"]

# 2. Q&A (login first)
login = requests.post(f"{BASE}/auth/login", json={
    "username": "admin", "password": "admin123"
})
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
qa = requests.post(f"{BASE}/search/qa", json={
    "question": "Admission requirements?", "top_k": 5
}, headers=headers)
print(qa.json()["answer"])

# 3. Upload + auto pipeline
with open("doc.pdf", "rb") as f:
    r = requests.post(f"{BASE}/inbox/upload",
        data={"domain": "regulations"},
        files={"files": ("doc.pdf", f, "application/pdf")}
    )
print(r.json())  # {"uploaded": ["doc.pdf"], "errors": []}`}
      </pre>
    </DocPage>
  );
}
