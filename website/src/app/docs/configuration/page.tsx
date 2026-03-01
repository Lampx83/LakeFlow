import { DocPage } from "@/components/docs/DocPage";

export default function ConfigurationPage() {
  return (
    <DocPage
      title="Configuration"
      prevHref="/docs/data-lake"
      prevLabel="Data Lake Architecture"
      nextHref="/docs/deployment"
      nextLabel="Deployment"
    >
      <p>
        LakeFlow uses a <code>.env</code> file in the repo root. Copy from <code>env.example</code> (or <code>.env.example</code>) then edit.
      </p>

      <h2>Environment variables</h2>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>Variable</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>HOST_LAKE_PATH</code></td>
            <td><strong>Required (Docker).</strong> Host path for volume bind mount. Maps to <code>/data</code> in container. Must exist before running <code>docker compose up</code>.</td>
          </tr>
          <tr>
            <td><code>LAKE_ROOT</code></td>
            <td>Data Lake root path in container/process. Docker: <code>/data</code>. Local: path you choose (e.g. <code>/Users/me/datalake</code>).</td>
          </tr>
          <tr>
            <td><code>QDRANT_HOST</code></td>
            <td>Qdrant host. Docker Compose: <code>lakeflow-qdrant</code>. Local: <code>localhost</code>. Portainer: <code>qdrant</code>.</td>
          </tr>
          <tr>
            <td><code>QDRANT_PORT</code></td>
            <td>Qdrant port. Default <code>6333</code>.</td>
          </tr>
          <tr>
            <td><code>API_BASE_URL</code></td>
            <td>Backend URL for Frontend. Docker: <code>http://lakeflow-backend:8011</code>. Local: <code>http://localhost:8011</code>. Frontend calls API via this URL.</td>
          </tr>
          <tr>
            <td><code>LAKEFLOW_MODE</code></td>
            <td><code>DEV</code> = show Pipeline Runner in UI, default password in login form. Omit or other = hide (production).</td>
          </tr>
          <tr>
            <td><code>LLM_BASE_URL</code></td>
            <td>Ollama URL for Q&amp;A, Admission agent, embedding (step3). E.g. <code>http://host:11434</code>. Backend must be able to reach it.</td>
          </tr>
          <tr>
            <td><code>LLM_MODEL</code></td>
            <td>LLM model. Default <code>qwen3:8b</code>. Used for Q&amp;A, Admission Agent.</td>
          </tr>
          <tr>
            <td><code>EMBED_MODEL</code></td>
            <td>Ollama embed model for step3 and Search API. Default <code>qwen3-embedding:8b</code>. Must match model used in step3 for search to work.</td>
          </tr>
          <tr>
            <td><code>EMBED_MODEL_OPTIONS</code></td>
            <td>Model list for step3 dropdown. Format: <code>qwen3-embedding:8b,nomic-embed-text,mxbai-embed-large</code>.</td>
          </tr>
          <tr>
            <td><code>OLLAMA_EMBED_URL</code></td>
            <td>Ollama embed API URL. Default: <code>$LLM_BASE_URL/api/embed</code>.</td>
          </tr>
          <tr>
            <td><code>OPENAI_API_KEY</code></td>
            <td>If set, Q&amp;A uses OpenAI instead of Ollama. Need <code>OPENAI_BASE_URL</code>, <code>OPENAI_MODEL</code> for custom endpoint.</td>
          </tr>
          <tr>
            <td><code>LAKEFLOW_MOUNT_DESCRIPTION</code></td>
            <td>Description shown in System Settings (e.g. &quot;Volume bind from /datalake/research&quot;).</td>
          </tr>
          <tr>
            <td><code>QDRANT_SERVICES</code></td>
            <td>Add Qdrant instances to UI dropdown. Format: <code>URL</code> or <code>Label|URL</code>, comma-separated.</td>
          </tr>
          <tr>
            <td><code>LAKEFLOW_PIPELINE_BASE_URL</code></td>
            <td>Backend URL for Inbox when auto-running pipeline (after upload). Default <code>http://127.0.0.1:8011</code>. In Docker Inbox runs from backend container so use localhost.</td>
          </tr>
          <tr>
            <td><code>LAKEFLOW_DATA_PATH</code></td>
            <td>Used in deploy: Data Lake path on server. Overrides <code>HOST_LAKE_PATH</code> when using <code>docker-compose.deploy.yml</code>.</td>
          </tr>
          <tr>
            <td><code>JWT_SECRET_KEY</code></td>
            <td>Secret for JWT. Production: set a secure value. Default dev-only.</td>
          </tr>
          <tr>
            <td><code>QDRANT_API_KEY</code></td>
            <td>Qdrant API key (if Qdrant Cloud or auth required).</td>
          </tr>
        </tbody>
      </table>

      <h2>Docker default values</h2>
      <p>In <code>docker-compose.yml</code>, backend/frontend receive:</p>
      <ul>
        <li><code>LAKE_ROOT=/data</code></li>
        <li><code>QDRANT_HOST=lakeflow-qdrant</code></li>
        <li><code>QDRANT_PORT=6333</code></li>
        <li><code>API_BASE_URL=http://lakeflow-backend:8011</code> (frontend)</li>
      </ul>
      <p>Volume <code>lakeflow_data</code> uses <code>device: $HOST_LAKE_PATH</code> — from <code>.env</code>.</p>

      <h2>Create zones</h2>
      <p>If zones don&apos;t exist, create them in the Data Lake directory:</p>
      <ul>
        <li><strong>Docker:</strong> Create under <code>HOST_LAKE_PATH</code> (maps to <code>/data</code> in container)</li>
        <li><strong>Local:</strong> Create under <code>LAKE_ROOT</code></li>
      </ul>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`# Replace $DATA_DIR with HOST_LAKE_PATH (Docker) or LAKE_ROOT (local)
mkdir -p $DATA_DIR/000_inbox $DATA_DIR/100_raw $DATA_DIR/200_staging \\
  $DATA_DIR/300_processed $DATA_DIR/400_embeddings $DATA_DIR/500_catalog`}
      </pre>

      <h2>Example .env</h2>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`# Docker dev (Ollama on host Mac/Win: use host.docker.internal)
HOST_LAKE_PATH=/Users/you/lakeflow_data
LAKE_ROOT=/data
QDRANT_HOST=lakeflow-qdrant
API_BASE_URL=http://lakeflow-backend:8011
LAKEFLOW_MODE=DEV
LLM_BASE_URL=http://host.docker.internal:11434
EMBED_MODEL=qwen3-embedding:8b

# Local dev
LAKE_ROOT=/Users/you/lakeflow_data
QDRANT_HOST=localhost
API_BASE_URL=http://localhost:8011
LAKEFLOW_MODE=DEV
LLM_BASE_URL=http://localhost:11434`}
      </pre>
    </DocPage>
  );
}
