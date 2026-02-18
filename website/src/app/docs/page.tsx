export default function DocsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-white">Documentation</h1>
      <p className="mt-4 text-white/70">
        LakeFlow documentation and guides. <strong>Website:</strong>{" "}
        <a
          href="https://lake-flow.vercel.app"
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand-400 hover:underline"
        >
          https://lake-flow.vercel.app
        </a>
      </p>
      <p className="mt-6 text-white/70">
        In the GitHub repository:
      </p>
      <ul className="mt-6 space-y-2 text-brand-400">
        <li>
          <a
            href="https://github.com/Lampx83/LakeFlow/blob/main/README.md"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            README — Overview and quick start
          </a>
        </li>
        <li>
          <a
            href="https://github.com/Lampx83/LakeFlow/blob/main/CONTRIBUTING.md"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            CONTRIBUTING.md — Developer setup, editable install
          </a>
        </li>
        <li>
          <a
            href="https://github.com/Lampx83/LakeFlow/tree/main/lake-flow/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            lake-flow/docs — API docs (embed, search)
          </a>
        </li>
        <li>
          <a
            href="https://pypi.org/project/lake-flow-pipeline/"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            PyPI — pip install lake-flow-pipeline (live 0.1.0)
          </a>
        </li>
      </ul>
      <div className="mt-12 rounded-xl border border-white/10 bg-white/5 p-6">
        <h2 className="text-lg font-semibold text-white">Quick commands</h2>
        <pre className="mt-3 font-mono text-sm text-brand-400">
{`# Install and run init (recommended)
pipx run lake-flow-pipeline init my-project

# Or with pip
pip install lake-flow-pipeline
lakeflow init my-project

# Developer setup (clone + editable)
git clone https://github.com/Lampx83/LakeFlow.git
cd LakeFlow/lake-flow
pip install -e ".[dev,full]"
`}
        </pre>
      </div>
    </div>
  );
}
