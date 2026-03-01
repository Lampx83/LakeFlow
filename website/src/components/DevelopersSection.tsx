"use client";

import { useLanguage } from "@/contexts/LanguageContext";

const resources = [
  {
    titleKey: "developers.quickStartTitle",
    descKey: "developers.quickStartDesc",
    href: "/#hero",
    command: "pipx run lake-flow-pipeline init",
  },
  {
    titleKey: "developers.docsTitle",
    descKey: "developers.docsDesc",
    href: "/docs",
  },
  {
    titleKey: "developers.githubTitle",
    descKey: "developers.githubDesc",
    href: "https://github.com/Lampx83/LakeFlow",
    external: true,
  },
  {
    titleKey: "developers.pypiTitle",
    descKey: "developers.pypiDesc",
    href: "https://pypi.org/project/lake-flow-pipeline/",
    external: true,
  },
];

export function DevelopersSection() {
  const { t } = useLanguage();
  return (
    <section
      id="developers"
      className="border-b border-white/10 bg-[#0a0a0f] px-4 py-20 sm:px-6 lg:px-8"
    >
      <div className="mx-auto max-w-7xl">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            {t("developers.title")}
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-white/70">
            {t("developers.subtitle")}
          </p>
        </div>
        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {resources.map((r) => (
            <a
              key={r.titleKey}
              href={r.href}
              target={r.external ? "_blank" : undefined}
              rel={r.external ? "noopener noreferrer" : undefined}
              className="group rounded-xl border border-white/10 bg-white/5 p-6 transition hover:border-brand-500/30 hover:bg-white/[0.07]"
            >
              <h3 className="font-semibold text-white group-hover:text-brand-400">
                {t(r.titleKey)}
              </h3>
              <p className="mt-2 text-sm text-white/70">{t(r.descKey)}</p>
              {r.command && (
                <code className="mt-3 block rounded bg-black/30 px-2 py-1.5 font-mono text-xs text-brand-400">
                  {r.command}
                </code>
              )}
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
