const features = [
  {
    title: "Layered Data Lake",
    description:
      "Zones: 000_inbox → 100_raw → 200_staging → 300_processed → 400_embeddings → 500_catalog. Hash, dedup, and catalog.",
    icon: "📁",
  },
  {
    title: "Semantic Search",
    description:
      "Query in natural language. Results by cosine similarity. Qdrant vector store with configurable collection.",
    icon: "🔍",
  },
  {
    title: "Embedding API",
    description:
      "POST /search/embed for text→vector. Compatible with external RAG/LLM services. Sentence-transformers support.",
    icon: "🧬",
  },
  {
    title: "Streamlit Control UI",
    description:
      "Run pipelines, explore data lake, test search. Multi–Qdrant support. Dev mode for Pipeline Runner.",
    icon: "🎛️",
  },
  {
    title: "Docker-first",
    description:
      "Backend, frontend, Qdrant via Docker Compose. No Python install on host. Mac M1 venv for GPU (Metal/MPS).",
    icon: "🐳",
  },
  {
    title: "Python & FastAPI",
    description:
      "Built with Python 3.10+, FastAPI, sentence-transformers, and Qdrant. Easy to extend and integrate.",
    icon: "🐍",
  },
];

export function ProductSection() {
  return (
    <section
      id="product"
      className="border-b border-white/10 bg-[#0a0a0f] px-4 py-20 sm:px-6 lg:px-8"
    >
      <div className="mx-auto max-w-7xl">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Everything you need for Data Lake & RAG
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-white/70">
            Ingest, process, embed, and search. One pipeline for RAG, LLM, and analytics.
          </p>
        </div>
        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="rounded-xl border border-white/10 bg-white/5 p-6 transition hover:border-brand-500/30 hover:bg-white/[0.07]"
            >
              <div className="text-2xl">{feature.icon}</div>
              <h3 className="mt-4 text-lg font-semibold text-white">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm text-white/70">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
