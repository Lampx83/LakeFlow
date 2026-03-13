"use client";

import { DocPage } from "@/components/docs/DocPage";
import { useLanguage } from "@/contexts/LanguageContext";

export default function FrontendUiPage() {
  const { t } = useLanguage();
  return (
    <DocPage
      titleKey="docs.pages.frontendUi.title"
      prevHref="/docs/backend-api"
      prevLabelKey="docs.sidebar.backendApi"
      nextHref="/docs/data-lake"
      nextLabelKey="docs.sidebar.dataLake"
    >
      <p>{t("docs.ui.intro")}</p>

      <h2>{t("docs.ui.loginTitle")}</h2>
      <p>{t("docs.ui.loginDefault")}</p>
      <p className="mt-1">{t("docs.ui.loginRequired")}</p>

      <h2>{t("docs.ui.pagesTitle")}</h2>
      <div className="space-y-6 mt-4">
        <div>
          <h3 className="text-lg font-semibold">{t("docs.ui.dashboard")}</h3>
          <p>{t("docs.ui.dashboardDesc")}</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">{t("docs.ui.dataLakeExplorer")}</h3>
          <p>{t("docs.ui.dataLakeExplorerDesc")}</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">{t("docs.ui.pipelineRunner")}</h3>
          <p><em>{t("docs.ui.pipelineRunnerOnly")}</em> {t("docs.ui.pipelineRunnerDesc")}</p>
          <ul className="list-disc pl-5 mt-1">
            <li>{t("docs.ui.pipelineOpt1")}</li>
            <li>{t("docs.ui.pipelineOpt2")}</li>
            <li>{t("docs.ui.pipelineOpt3")}</li>
            <li>{t("docs.ui.pipelineOpt4")}</li>
          </ul>
          <p className="mt-1">{t("docs.ui.pipelineResults")}</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">{t("docs.ui.sqliteViewer")}</h3>
          <p>{t("docs.ui.sqliteViewerDesc")}</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">{t("docs.ui.qdrantInspector")}</h3>
          <p>{t("docs.ui.qdrantInspectorDesc")}</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">{t("docs.ui.semanticSearch")}</h3>
          <p>{t("docs.ui.semanticSearchDesc")}</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">{t("docs.ui.qaWithAI")}</h3>
          <p>{t("docs.ui.qaWithAIDesc")}</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold">{t("docs.ui.systemSettings")}</h3>
          <p>{t("docs.ui.systemSettingsDesc")}</p>
        </div>
      </div>

      <h2>{t("docs.ui.multiQdrantTitle")}</h2>
      <p>{t("docs.ui.multiQdrantDesc")}</p>

      <h2>{t("docs.ui.frontendStructure")}</h2>
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

      <h2>{t("docs.ui.runLocally")}</h2>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`# From repo root
# dev_with_reload auto-loads .env from repo root
python frontend/streamlit/dev_with_reload.py

# Or run Streamlit directly (need .env or export vars)
streamlit run frontend/streamlit/app.py`}
      </pre>
      <p className="mt-2">{t("docs.ui.runLocallyNote")}</p>

      <h2>{t("docs.ui.troubleTitle")}</h2>
      <ul>
        <li><strong>{t("docs.ui.troubleConnection")}</strong> {t("docs.ui.troubleConnectionDesc")}</li>
        <li><strong>{t("docs.ui.troubleRunner")}</strong> {t("docs.ui.troubleRunnerDesc")}</li>
        <li><strong>{t("docs.ui.trouble401")}</strong> {t("docs.ui.trouble401Desc")}</li>
      </ul>
    </DocPage>
  );
}
