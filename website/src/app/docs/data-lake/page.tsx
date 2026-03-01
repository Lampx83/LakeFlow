import { DocPage } from "@/components/docs/DocPage";

export default function DataLakePage() {
  return (
    <DocPage
      title="Data Lake Architecture"
      prevHref="/docs/frontend-ui"
      prevLabel="Frontend (Streamlit)"
      nextHref="/docs/configuration"
      nextLabel="Configuration"
    >
      <p>
        LakeFlow uses a <strong>layered Data Lake</strong> with 6 zones. Data flow: inbox → raw → staging → processed → embeddings → Qdrant.
      </p>

      <h2>Inbox structure (000_inbox)</h2>
      <p>Place files in <code>000_inbox/&lt;domain&gt;/</code>. <code>domain</code> is a subfolder name (e.g. <code>regulations</code>, <code>syllabus</code>). Subpaths allowed: <code>000_inbox/domain/subfolder/subfolder2/</code>.</p>
      <p><strong>Supported formats:</strong> PDF, .docx, .xlsx, .xls, .pptx, .txt. Domain names use letters, numbers, <code>_</code>, <code>-</code> only.</p>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`000_inbox/
├── regulations/
│   ├── doc1.pdf
│   └── subfolder/doc2.docx
└── syllabus/
    └── course_a.pdf`}
      </pre>

      <h2>Zone descriptions</h2>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>Zone</th>
            <th>Path</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>000_inbox</code></td>
            <td><code>LAKE_ROOT/000_inbox</code></td>
            <td>Drop raw files here. step0 scans and moves to 100_raw. Organized by domain.</td>
          </tr>
          <tr>
            <td><code>100_raw</code></td>
            <td><code>LAKE_ROOT/100_raw</code></td>
            <td>step1: Copy + hash (SHA256) + dedup. Structure <code>&lt;domain&gt;/&lt;file_hash&gt;.pdf</code>. Writes catalog SQLite.</td>
          </tr>
          <tr>
            <td><code>200_staging</code></td>
            <td><code>LAKE_ROOT/200_staging</code></td>
            <td>step2: Extract text (pdf_analyzer, word_analyzer, excel_analyzer). Each file has <code>validation.json</code> with section structure.</td>
          </tr>
          <tr>
            <td><code>300_processed</code></td>
            <td><code>LAKE_ROOT/300_processed</code></td>
            <td>step2 output: Chunking → <code>chunks.json</code>. Each chunk has text, section_id, token_estimate. Ready for embedding.</td>
          </tr>
          <tr>
            <td><code>400_embeddings</code></td>
            <td><code>LAKE_ROOT/400_embeddings</code></td>
            <td>step3: Create <code>embedding.npy</code> via Ollama. Local cache before pushing to Qdrant.</td>
          </tr>
          <tr>
            <td><code>500_catalog</code></td>
            <td><code>LAKE_ROOT/500_catalog</code></td>
            <td>Metadata catalog (SQLite). Vectors stored in Qdrant (step4), not in 500_catalog.</td>
          </tr>
        </tbody>
      </table>

      <h2>Pipeline steps</h2>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>Step</th>
            <th>Script</th>
            <th>Input</th>
            <th>Output</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>step0</code></td>
            <td>step0_inbox.py</td>
            <td>000_inbox</td>
            <td>Scan inbox, ingestion → 100_raw (hash, dedup, write catalog). Can use <code>only_folders</code>.</td>
          </tr>
          <tr>
            <td><code>step1</code></td>
            <td>step1_raw.py</td>
            <td>000_inbox (via catalog)</td>
            <td>100_raw: copy file, hash, dedup</td>
          </tr>
          <tr>
            <td><code>step2</code></td>
            <td>step2_staging.py</td>
            <td>100_raw</td>
            <td>200_staging (validation.json), 300_processed (chunks.json)</td>
          </tr>
          <tr>
            <td><code>step3</code></td>
            <td>step3_processed_files.py</td>
            <td>300_processed</td>
            <td>400_embeddings: embedding.npy (Ollama). Model selectable via UI or <code>embed_model</code> in API.</td>
          </tr>
          <tr>
            <td><code>step4</code></td>
            <td>step3_processed_qdrant.py</td>
            <td>400_embeddings</td>
            <td>Push vectors to Qdrant collection. Can specify <code>collection_name</code>, <code>qdrant_url</code>.</td>
          </tr>
        </tbody>
      </table>

      <h2>Important file structures</h2>
      <ul>
        <li><code>validation.json</code> (200_staging): Metadata, sections, extracted text</li>
        <li><code>chunks.json</code> (300_processed): Array of chunks, each with <code>text</code>, <code>section_id</code>, <code>chunk_id</code>, <code>token_estimate</code></li>
        <li><code>embedding.npy</code> (400_embeddings): Numpy array of vectors, shape (n_chunks, dim)</li>
      </ul>

      <h2>Idempotency</h2>
      <p>Pipeline is idempotent: re-running same data yields deterministic UUIDs in Qdrant. Use <code>force_rerun</code> to overwrite cached results.</p>

      <h2>Supported formats (details)</h2>
      <p>PDF, Word (.docx), Excel (.xlsx, .xls), PPTX, TXT. Staging uses analyzers (pdf_analyzer, word_analyzer, excel_analyzer) to extract text and structure (tables, headings).</p>

      <h2>Run pipeline by domain</h2>
      <p>API <code>POST /pipeline/run/&#123;step&#125;</code> accepts <code>only_folders</code> — list of domains or file_hashes. Only processes selected folders.</p>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`# Run regulations domain only
{"only_folders": ["regulations"]}

# Run multiple domains
{"only_folders": ["regulations", "syllabus"]}`}
      </pre>

      <h2>NAS-friendly</h2>
      <p>SQLite uses non-WAL mode so it runs on Synology/NFS. Set <code>LAKE_ROOT</code> to point to path on NAS if needed.</p>
    </DocPage>
  );
}
