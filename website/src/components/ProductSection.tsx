"use client";

import { useLanguage } from "@/contexts/LanguageContext";

const featureKeys = [
  { titleKey: "product.f1Title", descKey: "product.f1Desc", icon: "⚙️" },
  { titleKey: "product.f2Title", descKey: "product.f2Desc", icon: "🖥️" },
  { titleKey: "product.f3Title", descKey: "product.f3Desc", icon: "📁" },
  { titleKey: "product.f4Title", descKey: "product.f4Desc", icon: "🔍" },
  { titleKey: "product.f5Title", descKey: "product.f5Desc", icon: "🐳" },
  { titleKey: "product.f6Title", descKey: "product.f6Desc", icon: "🐍" },
];

export function ProductSection() {
  const { t } = useLanguage();
  return (
    <section
      id="product"
      className="border-b border-white/10 bg-[#0a0a0f] px-4 py-20 sm:px-6 lg:px-8"
    >
      <div className="mx-auto max-w-7xl">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            {t("product.title")}
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-white/70">
            {t("product.subtitle")}
          </p>
        </div>
        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {featureKeys.map((f) => (
            <div
              key={f.titleKey}
              className="rounded-xl border border-white/10 bg-white/5 p-6 transition hover:border-brand-500/30 hover:bg-white/[0.07]"
            >
              <div className="text-2xl">{f.icon}</div>
              <h3 className="mt-4 text-lg font-semibold text-white">
                {t(f.titleKey)}
              </h3>
              <p className="mt-2 text-sm text-white/70">{t(f.descKey)}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
