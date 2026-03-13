"use client";

import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";

type DocPageProps = {
  title?: string;
  titleKey?: string;
  children: React.ReactNode;
  nextHref?: string;
  nextLabel?: string;
  nextLabelKey?: string;
  prevHref?: string;
  prevLabel?: string;
  prevLabelKey?: string;
};

export function DocPage({
  title,
  titleKey,
  children,
  nextHref,
  nextLabel,
  nextLabelKey,
  prevHref,
  prevLabel,
  prevLabelKey,
}: DocPageProps) {
  const { t } = useLanguage();
  const displayTitle = titleKey ? t(titleKey) : title ?? "";
  const displayNextLabel = nextLabelKey ? t(nextLabelKey) : nextLabel;
  const displayPrevLabel = prevLabelKey ? t(prevLabelKey) : prevLabel;

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 sm:px-8 lg:px-10">
      <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
        {displayTitle}
      </h1>
      <div className="docs-prose mt-8 text-white/80">
        {children}
      </div>
      {(prevHref || nextHref) && (
        <div className="mt-12 flex items-center justify-between border-t border-white/10 pt-8 text-sm text-white/50">
          <span>
            {prevHref && displayPrevLabel && (
              <Link href={prevHref} className="font-medium text-brand-400 hover:underline">
                ← {displayPrevLabel}
              </Link>
            )}
          </span>
          <span>
            {nextHref && displayNextLabel && (
              <Link href={nextHref} className="font-medium text-brand-400 hover:underline">
                {displayNextLabel} →
              </Link>
            )}
          </span>
        </div>
      )}
    </div>
  );
}
