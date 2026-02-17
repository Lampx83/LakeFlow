import Link from "next/link";

export function CtaSection() {
  return (
    <section className="border-b border-white/10 bg-gradient-to-b from-[#0d1117] to-[#0a0a0f] px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Ready to deploy?
        </h2>
        <p className="mt-4 text-lg text-white/70">
          Start with a free, self-hosted LakeFlow. Run in Docker in minutes.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/#hero"
            className="rounded-lg bg-brand-500 px-6 py-3 text-base font-semibold text-white transition hover:bg-brand-400"
          >
            Get Started
          </Link>
          <a
            href="https://github.com/Lampx83/LakeFlow"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-white/20 bg-white/5 px-6 py-3 text-base font-semibold text-white transition hover:bg-white/10"
          >
            View on GitHub
          </a>
        </div>
        <p className="mt-6 text-sm text-white/50">
          Open source. No account required. You own your data.
        </p>
      </div>
    </section>
  );
}
