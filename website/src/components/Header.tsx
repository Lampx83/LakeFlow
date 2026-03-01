"use client";

import Link from "next/link";
import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  BUILTIN_LOCALES,
  getLocaleLabel,
  getLocaleFlag,
  type BuiltinLocale,
} from "@/lib/i18n";

const navItems: { labelKey: string; href: string }[] = [
  { labelKey: "header.navProduct", href: "/#product" },
  { labelKey: "header.navSolutions", href: "/#solutions" },
  { labelKey: "header.navDevelopers", href: "/#developers" },
  { labelKey: "header.navDocs", href: "/docs" },
  { labelKey: "header.navAIPortal", href: "https://ai-portal-nine.vercel.app" },
];

export function Header() {
  const { t, locale, setLocale } = useLanguage();
  const [langOpen, setLangOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-[#0a0a0f]/95 backdrop-blur supports-[backdrop-filter]:bg-[#0a0a0f]/80">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="flex items-center gap-2 text-xl font-semibold text-white"
        >
          <span className="rounded bg-brand-500 px-1.5 py-0.5 font-mono text-sm font-bold text-white">
            Lake
          </span>
          Flow
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => (
            <Link
              key={item.labelKey}
              href={item.href}
              target={item.href.startsWith("http") ? "_blank" : undefined}
              rel={item.href.startsWith("http") ? "noopener noreferrer" : undefined}
              className="rounded-md px-3 py-2 text-sm font-medium text-white/80 transition hover:bg-white/5 hover:text-white"
            >
              {t(item.labelKey)}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              type="button"
              onClick={() => setLangOpen((o) => !o)}
              className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm text-white/70 hover:bg-white/5 hover:text-white"
              aria-label="Language"
              aria-expanded={langOpen}
            >
              <span className="text-lg leading-none" aria-hidden>
                {getLocaleFlag(locale)}
              </span>
              <span className="font-medium">{getLocaleLabel(locale)}</span>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {langOpen && (
              <>
                <div className="fixed inset-0 z-10" aria-hidden onClick={() => setLangOpen(false)} />
                <div className="absolute right-0 top-full z-20 mt-1 min-w-[160px] rounded-lg border border-white/10 bg-[#111] py-1 shadow-xl">
                  {BUILTIN_LOCALES.map((loc) => (
                    <button
                      key={loc}
                      type="button"
                      onClick={() => {
                        setLocale(loc as BuiltinLocale);
                        setLangOpen(false);
                      }}
                      className={`flex w-full items-center gap-2 px-4 py-2 text-left text-sm transition ${
                        locale === loc
                          ? "bg-brand-500/20 text-brand-400"
                          : "text-white/80 hover:bg-white/5 hover:text-white"
                      }`}
                    >
                      <span className="text-lg leading-none" aria-hidden>
                        {getLocaleFlag(loc)}
                      </span>
                      {getLocaleLabel(loc)}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
          <a
            href="https://github.com/Lampx83/LakeFlow"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden items-center gap-1.5 rounded-md px-3 py-2 text-sm text-white/70 hover:text-white sm:flex"
            aria-label="GitHub"
          >
            <GitHubIcon className="h-5 w-5" />
            <span>{t("header.navGitHub")}</span>
          </a>
          <Link
            href="/#hero"
            className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-400"
          >
            {t("header.getStarted")}
          </Link>
        </div>
      </div>
    </header>
  );
}

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="currentColor"
      viewBox="0 0 24 24"
      aria-hidden
    >
      <path
        fillRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
        clipRule="evenodd"
      />
    </svg>
  );
}
