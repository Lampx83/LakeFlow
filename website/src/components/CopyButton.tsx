"use client";

import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";

export function CopyButton({ text }: { text: string }) {
  const { t } = useLanguage();
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      type="button"
      onClick={copy}
      className="rounded-md border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/80 transition hover:bg-white/10 hover:text-white"
      aria-label={t("common.ariaCopy")}
    >
      {copied ? t("common.copied") : t("common.copy")}
    </button>
  );
}
