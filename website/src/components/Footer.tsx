import Link from "next/link";

const footerSections = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "/#product" },
      { label: "Data Lake", href: "/#product" },
      { label: "Roadmap", href: "https://github.com/Lampx83/LakeFlow" },
      { label: "Quick Start", href: "/#hero" },
    ],
  },
  {
    title: "Solutions",
    links: [
      { label: "For Developers", href: "/#solutions" },
      { label: "For Data Teams", href: "/#solutions" },
      { label: "Documentation", href: "/docs" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Docs", href: "/docs" },
      { label: "GitHub", href: "https://github.com/Lampx83/LakeFlow" },
      { label: "PyPI: lake-flow-pipeline", href: "https://pypi.org/project/lake-flow-pipeline/" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "/#about" },
      { label: "License", href: "https://github.com/Lampx83/LakeFlow/blob/main/LICENSE" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-[#070708]">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {footerSections.map((section) => (
            <div key={section.title}>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-white/90">
                {section.title}
              </h3>
              <ul className="mt-4 space-y-3">
                {section.links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      target={link.href.startsWith("http") ? "_blank" : undefined}
                      rel={link.href.startsWith("http") ? "noopener noreferrer" : undefined}
                      className="text-sm text-white/60 transition hover:text-brand-400"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-8 sm:flex-row">
          <div className="flex items-center gap-2 text-sm text-white/60">
            <span className="rounded bg-brand-500/20 px-1.5 py-0.5 font-mono text-xs font-bold text-brand-400">
              LakeFlow
            </span>
            — Open source. Free to use.
          </div>
          <div className="flex gap-6 text-sm text-white/60">
            <a
              href="https://github.com/Lampx83/LakeFlow"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-brand-400"
            >
              GitHub
            </a>
            <Link href="/docs" className="hover:text-brand-400">
              Docs
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
