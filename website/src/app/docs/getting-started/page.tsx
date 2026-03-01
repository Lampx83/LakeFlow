"use client";

import { DocPage } from "@/components/docs/DocPage";
import { useLanguage } from "@/contexts/LanguageContext";

const URL_BACKEND = "http://localhost:8011";
const URL_FRONTEND = "http://localhost:8012";
const URL_QDRANT = "http://localhost:8013";

export default function GettingStartedPage() {
  const { t } = useLanguage();
  return (
    <DocPage
      titleKey="docs.pages.gettingStarted.title"
      nextHref="/docs/backend-api"
      nextLabelKey="docs.sidebar.backendApi"
    >
      <h2>{t("docs.gs.sysReqsTitle")}</h2>
      <ul>
        <li>{t("docs.gs.sysReqs1")}</li>
        <li>{t("docs.gs.sysReqs2")}</li>
        <li>{t("docs.gs.sysReqs3")}</li>
      </ul>

      <h2>{t("docs.gs.quickInstallTitle")}</h2>
      <p>{t("docs.gs.quickInstallIntro")}</p>
      <ol className="list-decimal space-y-2 pl-5 mt-2">
        <li><strong>{t("docs.gs.cloneEnv")}</strong></li>
      </ol>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`git clone https://github.com/Lampx83/LakeFlow.git LakeFlow
cd LakeFlow
cp env.example .env   # or cp .env.example .env`}
      </pre>
      <ol className="list-decimal space-y-2 pl-5 mt-2" start={2}>
        <li><strong>{t("docs.gs.required")}</strong> {t("docs.gs.requiredDesc")}
          <ul className="mt-1 list-disc pl-5">
            <li>{t("docs.gs.macosExample")} <code>HOST_LAKE_PATH=/Users/you/lakeflow_data</code></li>
            <li>{t("docs.gs.linuxExample")} <code>HOST_LAKE_PATH=/datalake/research</code></li>
          </ul>
          {t("docs.gs.dirMustExist")}
        </li>
        <li>{t("docs.gs.createDir")} <code>mkdir -p $HOST_LAKE_PATH</code></li>
        <li>{t("docs.gs.createZones")} <code>mkdir -p $HOST_LAKE_PATH/000_inbox $HOST_LAKE_PATH/100_raw $HOST_LAKE_PATH/200_staging $HOST_LAKE_PATH/300_processed $HOST_LAKE_PATH/400_embeddings $HOST_LAKE_PATH/500_catalog</code></li>
        <li>{t("docs.gs.runDocker")} <code>docker compose up --build</code> {t("docs.gs.orBackground")}</li>
      </ol>
      <p className="mt-2 text-amber-200/90"><strong>{t("docs.gs.note")}</strong> {t("docs.gs.noteDockerDesc")}</p>
      <p className="mt-3">{t("docs.gs.afterStartup")}</p>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr><th>{t("docs.gs.service")}</th><th>{t("docs.gs.url")}</th><th>{t("docs.gs.notes")}</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>{t("docs.gs.backendApi")}</td>
            <td><a href={URL_BACKEND} target="_blank" rel="noopener noreferrer" className="text-brand-400">{URL_BACKEND}</a></td>
            <td>{t("docs.gs.baseUrlApi")}</td>
          </tr>
          <tr>
            <td>{t("docs.gs.swaggerUi")}</td>
            <td><a href={`${URL_BACKEND}/docs`} target="_blank" rel="noopener noreferrer" className="text-brand-400">{URL_BACKEND}/docs</a></td>
            <td>{t("docs.gs.interactiveApi")}</td>
          </tr>
          <tr>
            <td>{t("docs.gs.streamlitUi")}</td>
            <td><a href={URL_FRONTEND} target="_blank" rel="noopener noreferrer" className="text-brand-400">{URL_FRONTEND}</a></td>
            <td>{t("docs.gs.loginCreds")} <code>admin</code> / <code>admin123</code></td>
          </tr>
          <tr>
            <td>{t("docs.gs.qdrant")}</td>
            <td>{URL_QDRANT}</td>
            <td>{t("docs.gs.vectorDbNote")}</td>
          </tr>
        </tbody>
      </table>

      <h2>{t("docs.gs.projectStructure")}</h2>
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

      <h2>{t("docs.gs.localDevTitle")}</h2>
      <p>{t("docs.gs.localDevIntro")}</p>
      <ol className="list-decimal space-y-2 pl-5 mt-2">
        <li><strong>{t("docs.gs.qdrantStep")}</strong> <code>docker compose up -d qdrant</code></li>
        <li><strong>{t("docs.gs.backendStep")}</strong>
          <pre className="mt-1 overflow-x-auto rounded border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs text-brand-400">{`cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install torch           # Mac M1: install first for Metal (MPS)
pip install -r requirements.txt && pip install -e .
uvicorn lakeflow.main:app --reload --port 8011`}</pre>
        </li>
        <li><strong>{t("docs.gs.frontendStep")}</strong> {t("docs.gs.frontendFromRoot")}
          <pre className="mt-1 overflow-x-auto rounded border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs text-brand-400">{`python frontend/streamlit/dev_with_reload.py
# or: streamlit run frontend/streamlit/app.py`}</pre>
        </li>
      </ol>
      <p className="mt-2">{t("docs.gs.envNeeds")}</p>

      <h2>{t("docs.gs.firstRunTitle")}</h2>
      <ol className="list-decimal space-y-2 pl-5">
        <li><strong>{t("docs.gs.createZonesStep")}</strong> <code>mkdir -p $HOST_LAKE_PATH/000_inbox $HOST_LAKE_PATH/100_raw $HOST_LAKE_PATH/200_staging $HOST_LAKE_PATH/300_processed $HOST_LAKE_PATH/400_embeddings $HOST_LAKE_PATH/500_catalog</code></li>
        <li><strong>{t("docs.gs.addFilesStep")}</strong> {t("docs.gs.addFilesDesc")}</li>
        <li><strong>{t("docs.gs.runPipelineStep")}</strong> {t("docs.gs.runPipelineDesc")}</li>
        <li><strong>{t("docs.gs.testSearchStep")}</strong> {t("docs.gs.testSearchDesc")}</li>
      </ol>
      <p className="mt-2 text-amber-200/90"><strong>{t("docs.gs.note")}</strong> {t("docs.gs.noteStep3")}</p>

      <h2>{t("docs.gs.macM1Title")}</h2>
      <p>{t("docs.gs.macM1Desc")}</p>

      <h2>{t("docs.gs.buildNoGpuTitle")}</h2>
      <p>{t("docs.gs.buildNoGpuDesc")} <code>DOCKER_BUILDKIT=1 docker compose up --build</code></p>

      <h2>{t("docs.gs.troubleshootTitle")}</h2>
      <ul>
        <li><strong>{t("docs.gs.troubleCompose")}</strong> {t("docs.gs.troubleComposeDesc")}</li>
        <li><strong>{t("docs.gs.troubleFrontend")}</strong> {t("docs.gs.troubleFrontendDesc")}</li>
        <li><strong>{t("docs.gs.troubleSearch")}</strong> {t("docs.gs.troubleSearchDesc")}</li>
      </ul>
    </DocPage>
  );
}
