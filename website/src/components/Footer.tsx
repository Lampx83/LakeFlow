"use client";

import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";

const footerSections = [
  {
    titleKey: "footer.product",
    links: [
      { labelKey: "footer.features", href: "/#product" },
      { labelKey: "footer.dataLake", href: "/#product" },
      { labelKey: "footer.roadmap", href: "https://github.com/Lampx83/LakeFlow" },
      { labelKey: "footer.quickStart", href: "/#hero" },
    ],
  },
  {
    titleKey: "footer.solutions",
    links: [
      { labelKey: "footer.forDevelopers", href: "/#solutions" },
      { labelKey: "footer.forDataTeams", href: "/#solutions" },
      { labelKey: "footer.documentation", href: "/docs" },
    ],
  },
  {
    titleKey: "footer.resources",
    links: [
      { labelKey: "footer.docs", href: "/docs" },
      { labelKey: "footer.aiPortal", href: "https://ai-portal-nine.vercel.app" },
      { labelKey: "footer.github", href: "https://github.com/Lampx83/LakeFlow" },
      { labelKey: "footer.pypi", href: "https://pypi.org/project/lake-flow-pipeline/" },
    ],
  },
  {
    titleKey: "footer.company",
    links: [
      { labelKey: "footer.about", href: "/#about" },
      { labelKey: "footer.license", href: "https://github.com/Lampx83/LakeFlow/blob/main/LICENSE" },
    ],
  },
];

export function Footer() {
  const { t } = useLanguage();
  return (
    <footer className="border-t border-white/10 bg-[#070708]">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {footerSections.map((section) => (
            <div key={section.titleKey}>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-white/90">
                {t(section.titleKey)}
              </h3>
              <ul className="mt-4 space-y-3">
                {section.links.map((link) => (
                  <li key={link.labelKey}>
                    <a
                      href={link.href}
                      target={link.href.startsWith("http") ? "_blank" : undefined}
                      rel={link.href.startsWith("http") ? "noopener noreferrer" : undefined}
                      className="text-sm text-white/60 transition hover:text-brand-400"
                    >
                      {t(link.labelKey)}
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
            — {t("footer.taglineEcosystem")}{" "}
            <a
              href="https://ai-portal-nine.vercel.app"
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-400 hover:underline"
            >
              AI Portal
            </a>
            . {t("footer.tagline")}
          </div>
          <div className="flex gap-6 text-sm text-white/60">
            <a
              href="https://github.com/Lampx83/LakeFlow"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-brand-400"
            >
              {t("footer.github")}
            </a>
            <Link href="/docs" className="hover:text-brand-400">
              {t("footer.docs")}
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
