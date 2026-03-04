"use client";

import { DocPage } from "@/components/docs/DocPage";
import { useLanguage } from "@/contexts/LanguageContext";

export default function ConfigurationPage() {
  const { t } = useLanguage();
  return (
    <DocPage
      titleKey="docs.pages.configuration.title"
      prevHref="/docs/data-lake"
      prevLabelKey="docs.sidebar.dataLake"
      nextHref="/docs/deployment"
      nextLabelKey="docs.sidebar.deployment"
    >
      <p>{t("docs.config.intro")}</p>

      <h2>{t("docs.config.envVarsTitle")}</h2>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>{t("docs.config.varCol")}</th>
            <th>{t("docs.config.descCol")}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>HOST_LAKE_PATH</code></td>
            <td><strong>{t("docs.config.hostLakePath")}</strong></td>
          </tr>
          <tr>
            <td><code>LAKE_ROOT</code></td>
            <td>{t("docs.config.lakeRoot")}</td>
          </tr>
          <tr>
            <td><code>QDRANT_HOST</code></td>
            <td>{t("docs.config.qdrantHost")}</td>
          </tr>
          <tr>
            <td><code>QDRANT_PORT</code></td>
            <td>{t("docs.config.qdrantPort")}</td>
          </tr>
          <tr>
            <td><code>API_BASE_URL</code></td>
            <td>{t("docs.config.apiBaseUrl")}</td>
          </tr>
          <tr>
            <td><code>LAKEFLOW_MODE</code></td>
            <td>{t("docs.config.lakeflowMode")}</td>
          </tr>
          <tr>
            <td><code>LLM_BASE_URL</code></td>
            <td>{t("docs.config.llmBaseUrl")}</td>
          </tr>
          <tr>
            <td><code>LLM_MODEL</code></td>
            <td>{t("docs.config.llmModel")}</td>
          </tr>
          <tr>
            <td><code>EMBED_MODEL</code></td>
            <td>{t("docs.config.embedModel")}</td>
          </tr>
          <tr>
            <td><code>EMBED_MODEL_OPTIONS</code></td>
            <td>{t("docs.config.embedModelOptions")}</td>
          </tr>
          <tr>
            <td><code>OLLAMA_EMBED_URL</code></td>
            <td>{t("docs.config.ollamaEmbedUrl")}</td>
          </tr>
          <tr>
            <td><code>OPENAI_API_KEY</code></td>
            <td>{t("docs.config.openaiKey")}</td>
          </tr>
          <tr>
            <td><code>LAKEFLOW_MOUNT_DESCRIPTION</code></td>
            <td>{t("docs.config.mountDesc")}</td>
          </tr>
          <tr>
            <td><code>QDRANT_SERVICES</code></td>
            <td>{t("docs.config.qdrantServices")}</td>
          </tr>
          <tr>
            <td><code>LAKEFLOW_PIPELINE_BASE_URL</code></td>
            <td>{t("docs.config.pipelineBaseUrl")}</td>
          </tr>
          <tr>
            <td><code>LAKEFLOW_DATA_PATH</code></td>
            <td>{t("docs.config.dataPath")}</td>
          </tr>
          <tr>
            <td><code>JWT_SECRET_KEY</code></td>
            <td>{t("docs.config.jwtSecret")}</td>
          </tr>
          <tr>
            <td><code>QDRANT_API_KEY</code></td>
            <td>{t("docs.config.qdrantApiKey")}</td>
          </tr>
        </tbody>
      </table>

      <h2>{t("docs.config.dockerDefaultsTitle")}</h2>
      <p>{t("docs.config.dockerDefaultsIntro")}</p>
      <ul>
        <li><code>{t("docs.config.dockerDefaults1")}</code></li>
        <li><code>{t("docs.config.dockerDefaults2")}</code></li>
        <li><code>{t("docs.config.dockerDefaults3")}</code></li>
        <li><code>{t("docs.config.dockerDefaults4")}</code></li>
      </ul>
      <p>{t("docs.config.volumeNote")}</p>

      <h2>{t("docs.config.createZonesTitle")}</h2>
      <p>{t("docs.config.createZonesIntro")}</p>
      <ul>
        <li><strong>Docker:</strong> {t("docs.config.createZonesDocker")}</li>
        <li><strong>Local:</strong> {t("docs.config.createZonesLocal")}</li>
      </ul>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`# Replace $DATA_DIR with HOST_LAKE_PATH (Docker) or LAKE_ROOT (local)
mkdir -p $DATA_DIR/000_inbox $DATA_DIR/100_raw $DATA_DIR/200_staging \\
  $DATA_DIR/300_processed $DATA_DIR/400_embeddings $DATA_DIR/500_catalog`}
      </pre>

      <h2>{t("docs.config.exampleEnvTitle")}</h2>
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
