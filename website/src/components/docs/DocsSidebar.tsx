"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "@/contexts/LanguageContext";

const navItems: { href: string; labelKey: string }[] = [
  { href: "/docs", labelKey: "docs.sidebar.intro" },
  { href: "/docs/getting-started", labelKey: "docs.sidebar.gettingStarted" },
  { href: "/docs/backend-api", labelKey: "docs.sidebar.backendApi" },
  { href: "/docs/frontend-ui", labelKey: "docs.sidebar.frontendUi" },
  { href: "/docs/data-lake", labelKey: "docs.sidebar.dataLake" },
  { href: "/docs/configuration", labelKey: "docs.sidebar.configuration" },
  { href: "/docs/deployment", labelKey: "docs.sidebar.deployment" },
];

export function DocsSidebar() {
  const pathname = usePathname();
  const { t } = useLanguage();

  return (
    <aside className="w-56 shrink-0 border-r border-white/10 bg-[#070708]/80">
      <nav className="sticky top-20 flex flex-col gap-0.5 py-6 pl-6 pr-3">
        <Link
          href="/docs"
          className="mb-2 text-xs font-semibold uppercase tracking-wider text-white/50"
        >
          {t("docs.sidebar.documentation")}
        </Link>
        {navItems.map((item) => {
          const isActive =
            item.href === "/docs"
              ? pathname === "/docs"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-2 text-sm transition ${
                isActive
                  ? "bg-brand-500/20 font-medium text-brand-400"
                  : "text-white/70 hover:bg-white/5 hover:text-white"
              }`}
            >
              {t(item.labelKey)}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
