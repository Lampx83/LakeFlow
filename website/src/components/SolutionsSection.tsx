"use client";

import { useLanguage } from "@/contexts/LanguageContext";

const solutions = [
  {
    titleKey: "solutions.devTitle",
    descKey: "solutions.devDesc",
    ctaKey: "solutions.devCta",
    href: "/#hero",
  },
  {
    titleKey: "solutions.teamsTitle",
    descKey: "solutions.teamsDesc",
    ctaKey: "solutions.teamsCta",
    href: "/docs",
  },
  {
    titleKey: "solutions.enterpriseTitle",
    descKey: "solutions.enterpriseDesc",
    ctaKey: "solutions.enterpriseCta",
    href: "/docs/deployment",
  },
];

export function SolutionsSection() {
  const { t } = useLanguage();
  return (
    <section
      id="solutions"
      className="border-b border-white/10 bg-[#070708] px-4 py-20 sm:px-6 lg:px-8"
    >
      <div className="mx-auto max-w-7xl">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            {t("solutions.title")}
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-white/70">
            {t("solutions.subtitle")}
          </p>
        </div>
        <div className="mt-16 grid gap-8 md:grid-cols-3">
          {solutions.map((sol) => (
            <div
              key={sol.titleKey}
              className="rounded-xl border border-white/10 bg-[#0a0a0f] p-6"
            >
              <h3 className="text-xl font-semibold text-white">{t(sol.titleKey)}</h3>
              <p className="mt-3 text-white/70">{t(sol.descKey)}</p>
              <a
                href={sol.href}
                className="mt-4 inline-block text-sm font-medium text-brand-400 hover:text-brand-300"
              >
                {t(sol.ctaKey)} →
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
