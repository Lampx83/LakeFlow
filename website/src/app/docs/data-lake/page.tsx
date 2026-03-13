"use client";

import { DocPage } from "@/components/docs/DocPage";
import { useLanguage } from "@/contexts/LanguageContext";

export default function DataLakePage() {
  const { t } = useLanguage();
  return (
    <DocPage
      titleKey="docs.pages.dataLake.title"
      prevHref="/docs/frontend-ui"
      prevLabelKey="docs.sidebar.frontendUi"
      nextHref="/docs/configuration"
      nextLabelKey="docs.sidebar.configuration"
    >
      <p>{t("docs.dl.intro")}</p>

      <h2>{t("docs.dl.inboxTitle")}</h2>
      <p>{t("docs.dl.inboxPlace")}</p>
      <p>{t("docs.dl.supportedFormats")}</p>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`000_inbox/
├── regulations/
│   ├── doc1.pdf
│   └── subfolder/doc2.docx
└── syllabus/
    └── course_a.pdf`}
      </pre>

      <h2>{t("docs.dl.zoneTitle")}</h2>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>{t("docs.dl.zoneCol")}</th>
            <th>{t("docs.dl.pathCol")}</th>
            <th>{t("docs.dl.descCol")}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>000_inbox</code></td>
            <td><code>LAKE_ROOT/000_inbox</code></td>
            <td>{t("docs.dl.inboxDesc")}</td>
          </tr>
          <tr>
            <td><code>100_raw</code></td>
            <td><code>LAKE_ROOT/100_raw</code></td>
            <td>{t("docs.dl.rawDesc")}</td>
          </tr>
          <tr>
            <td><code>200_staging</code></td>
            <td><code>LAKE_ROOT/200_staging</code></td>
            <td>{t("docs.dl.stagingDesc")}</td>
          </tr>
          <tr>
            <td><code>300_processed</code></td>
            <td><code>LAKE_ROOT/300_processed</code></td>
            <td>{t("docs.dl.processedDesc")}</td>
          </tr>
          <tr>
            <td><code>400_embeddings</code></td>
            <td><code>LAKE_ROOT/400_embeddings</code></td>
            <td>{t("docs.dl.embeddingsDesc")}</td>
          </tr>
          <tr>
            <td><code>500_catalog</code></td>
            <td><code>LAKE_ROOT/500_catalog</code></td>
            <td>{t("docs.dl.catalogDesc")}</td>
          </tr>
        </tbody>
      </table>

      <h2>{t("docs.dl.pipelineTitle")}</h2>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>{t("docs.dl.stepCol")}</th>
            <th>{t("docs.dl.scriptCol")}</th>
            <th>{t("docs.dl.inputCol")}</th>
            <th>{t("docs.dl.outputCol")}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>step0</code></td>
            <td>step0_inbox.py</td>
            <td>000_inbox</td>
            <td>{t("docs.dl.step0Out")}</td>
          </tr>
          <tr>
            <td><code>step1</code></td>
            <td>step1_raw.py</td>
            <td>000_inbox (via catalog)</td>
            <td>{t("docs.dl.step1Out")}</td>
          </tr>
          <tr>
            <td><code>step2</code></td>
            <td>step2_staging.py</td>
            <td>100_raw</td>
            <td>{t("docs.dl.step2Out")}</td>
          </tr>
          <tr>
            <td><code>step3</code></td>
            <td>step3_processed_files.py</td>
            <td>300_processed</td>
            <td>{t("docs.dl.step3Out")}</td>
          </tr>
          <tr>
            <td><code>step4</code></td>
            <td>step3_processed_qdrant.py</td>
            <td>400_embeddings</td>
            <td>{t("docs.dl.step4Out")}</td>
          </tr>
        </tbody>
      </table>

      <h2>{t("docs.dl.fileStructTitle")}</h2>
      <ul>
        <li>{t("docs.dl.fileStruct1")}</li>
        <li>{t("docs.dl.fileStruct2")}</li>
        <li>{t("docs.dl.fileStruct3")}</li>
      </ul>

      <h2>{t("docs.dl.idempotencyTitle")}</h2>
      <p>{t("docs.dl.idempotencyDesc")}</p>

      <h2>{t("docs.dl.formatsTitle")}</h2>
      <p>{t("docs.dl.formatsDesc")}</p>

      <h2>{t("docs.dl.runByDomainTitle")}</h2>
      <p>{t("docs.dl.runByDomainDesc")}</p>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`# Run regulations domain only
{"only_folders": ["regulations"]}

# Run multiple domains
{"only_folders": ["regulations", "syllabus"]}`}
      </pre>

      <h2>{t("docs.dl.nasTitle")}</h2>
      <p>{t("docs.dl.nasDesc")}</p>
    </DocPage>
  );
}
