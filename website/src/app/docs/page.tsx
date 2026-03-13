"use client";

import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";

const sectionCards = [
  { href: "/docs/getting-started", labelKey: "docs.intro.card1Label", descKey: "docs.intro.card1Desc" },
  { href: "/docs/backend-api", labelKey: "docs.intro.card2Label", descKey: "docs.intro.card2Desc" },
  { href: "/docs/frontend-ui", labelKey: "docs.intro.card3Label", descKey: "docs.intro.card3Desc" },
  { href: "/docs/data-lake", labelKey: "docs.intro.card4Label", descKey: "docs.intro.card4Desc" },
  { href: "/docs/configuration", labelKey: "docs.intro.card5Label", descKey: "docs.intro.card5Desc" },
  { href: "/docs/deployment", labelKey: "docs.intro.card6Label", descKey: "docs.intro.card6Desc" },
];

export default function DocsIntroPage() {
  const { t } = useLanguage();
  return (
    <div className="mx-auto max-w-3xl px-6 py-12 sm:px-8 lg:px-10">
      <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
        {t("docs.intro.title")}
      </h1>
      <p className="mt-4 text-lg text-white/80">
        {t("docs.intro.paragraph")}
      </p>

      <h2 className="mt-10 text-xl font-semibold text-white">
        {t("docs.intro.prereqTitle")}
      </h2>
      <ul className="mt-4 list-disc space-y-1 pl-5 text-white/80">
        <li>{t("docs.intro.prereq1")}</li>
        <li>{t("docs.intro.prereq2")}</li>
        <li>{t("docs.intro.prereq3")}</li>
        <li>{t("docs.intro.prereq4")}</li>
      </ul>

      <h2 className="mt-10 text-xl font-semibold text-white">
        {t("docs.intro.orderTitle")}
      </h2>
      <ol className="mt-4 list-decimal space-y-2 pl-5 text-white/80">
        <li>{t("docs.intro.order1")}</li>
        <li>{t("docs.intro.order2")}</li>
        <li>{t("docs.intro.order3")}</li>
        <li>{t("docs.intro.order4")}</li>
      </ol>

      <h2 className="mt-10 text-xl font-semibold text-white">
        {t("docs.intro.checklistTitle")}
      </h2>
      <ul className="mt-4 list-disc space-y-1 pl-5 text-white/80">
        <li>{t("docs.intro.check1")}</li>
        <li>{t("docs.intro.check2")}</li>
        <li>{t("docs.intro.check3")}</li>
        <li>{t("docs.intro.check4")}</li>
        <li>{t("docs.intro.check5")}</li>
      </ul>

      <h2 className="mt-10 text-xl font-semibold text-white">
        {t("docs.intro.topicsTitle")}
      </h2>
      <p className="mt-2 text-white/70">
        {t("docs.intro.topicsSub")}
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {sectionCards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group rounded-xl border border-white/10 bg-white/5 p-5 transition hover:border-brand-500/30 hover:bg-white/[0.07]"
          >
            <h3 className="font-semibold text-white group-hover:text-brand-400">
              {t(card.labelKey)}
            </h3>
            <p className="mt-2 text-sm text-white/70">{t(card.descKey)}</p>
            <span className="mt-2 inline-block text-sm font-medium text-brand-400">
              {t("docs.intro.readMore")} →
            </span>
          </Link>
        ))}
      </div>

      <h2 className="mt-10 text-xl font-semibold text-white">
        {t("docs.intro.troubleshootTitle")}
      </h2>
      <ul className="mt-4 list-disc space-y-1 pl-5 text-white/80">
        <li>{t("docs.intro.trouble1")}</li>
        <li>{t("docs.intro.trouble2")}</li>
        <li>{t("docs.intro.trouble3")}</li>
        <li>{t("docs.intro.trouble4")}</li>
      </ul>

      <h2 className="mt-10 text-xl font-semibold text-white">
        {t("docs.intro.tipsTitle")}
      </h2>
      <ul className="mt-4 list-disc space-y-1 pl-5 text-white/80">
        <li>{t("docs.intro.tip1")}</li>
        <li>{t("docs.intro.tip2")}</li>
        <li>{t("docs.intro.tip3")}</li>
        <li>{t("docs.intro.tip4")}</li>
      </ul>

      <div className="mt-12 rounded-lg border border-white/10 bg-white/5 p-5">
        <h3 className="font-semibold text-white">{t("docs.intro.quickLinks")}</h3>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-white/70">
          <li>
            <a href="https://github.com/Lampx83/LakeFlow" target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:underline">
              {t("docs.intro.github")}
            </a>
          </li>
          <li>
            <a href="https://pypi.org/project/lake-flow-pipeline/" target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:underline">
              {t("docs.intro.pypi")}
            </a>
          </li>
          <li>{t("docs.intro.swaggerUi")}</li>
          <li>{t("docs.intro.redoc")}</li>
        </ul>
      </div>

      <div className="mt-8 flex items-center gap-2 text-sm text-white/50">
        <span>{t("docs.intro.next")}</span>
        <Link href="/docs/getting-started" className="font-medium text-brand-400 hover:underline">
          {t("docs.sidebar.gettingStarted")} →
        </Link>
      </div>
    </div>
  );
}
