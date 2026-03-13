"use client";

import Link from "next/link";
import { CopyButton } from "./CopyButton";
import { useLanguage } from "@/contexts/LanguageContext";

const COMMAND = "pipx run lake-flow-pipeline init";

export function Hero() {
  const { t } = useLanguage();
  return (
    <section
      id="hero"
      className="relative overflow-hidden border-b border-white/10 bg-gradient-to-b from-[#0a0a0f] via-[#0d1117] to-[#0a0a0f] px-4 pt-16 pb-24 sm:px-6 sm:pt-20 sm:pb-28 lg:px-8 lg:pt-24 lg:pb-32"
    >
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1.5 text-sm text-brand-400">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-brand-500" />
          </span>
          {t("hero.badge")}
        </div>
      </div>

      <div className="mx-auto max-w-4xl text-center">
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl md:text-6xl lg:text-7xl">
          {t("hero.titleBefore")}
          <span className="gradient-text">{t("hero.titleHighlight")}</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-white/70 sm:text-xl">
          {t("hero.subtitle")}
        </p>

        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <div className="flex w-full max-w-md items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400 sm:max-w-lg">
            <code className="break-all">docker compose up --build</code>
            <CopyButton text="docker compose up --build" />
          </div>
        </div>
        <p className="mt-3 text-sm text-white/50">{t("hero.or")} <code className="text-brand-400">{COMMAND}</code></p>
        <Link
          href="#product"
          className="mt-2 inline-flex rounded-lg bg-brand-500 px-6 py-3 text-base font-semibold text-white transition hover:bg-brand-400"
        >
          {t("hero.getStarted")}
        </Link>
      </div>

      <div
        className="pointer-events-none absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)`,
          backgroundSize: "64px 64px",
        }}
      />
    </section>
  );
}
