"use client";

import Link from "next/link";
import { useState } from "react";

const navItems = [
  {
    label: "Product",
    href: "/#product",
    children: [
      { label: "Features", href: "/#product" },
      { label: "Data Lake", href: "/#product" },
      { label: "RAG & Embedding", href: "/#product" },
      { label: "Docker", href: "/#product" },
    ],
  },
  {
    label: "Solutions",
    href: "/#solutions",
    children: [
      { label: "For Developers", href: "/#solutions" },
      { label: "For Data Teams", href: "/#solutions" },
      { label: "Enterprise", href: "/#solutions" },
    ],
  },
  {
    label: "Developers",
    href: "/#developers",
    children: [
      { label: "Quick Start", href: "/#hero" },
      { label: "Documentation", href: "/docs" },
      { label: "GitHub", href: "https://github.com/Lampx83/LakeFlow" },
    ],
  },
  { label: "Docs", href: "/docs" },
];

export function Header() {
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

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
          {navItems.map((item) =>
            item.children ? (
              <div
                key={item.label}
                className="relative"
                onMouseEnter={() => setOpenDropdown(item.label)}
                onMouseLeave={() => setOpenDropdown(null)}
              >
                <button
                  className="flex items-center gap-0.5 rounded-md px-3 py-2 text-sm font-medium text-white/80 transition hover:bg-white/5 hover:text-white"
                  onClick={() => setOpenDropdown(openDropdown === item.label ? null : item.label)}
                >
                  {item.label}
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                {openDropdown === item.label && (
                  <div className="absolute left-0 top-full pt-1">
                    <div className="min-w-[180px] rounded-lg border border-white/10 bg-[#111] py-1 shadow-xl">
                      {item.children.map((child) => (
                        <Link
                          key={child.label}
                          href={child.href}
                          target={child.href.startsWith("http") ? "_blank" : undefined}
                          rel={child.href.startsWith("http") ? "noopener noreferrer" : undefined}
                          className="block px-4 py-2 text-sm text-white/80 hover:bg-white/5 hover:text-white"
                          onClick={() => setOpenDropdown(null)}
                        >
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <Link
                key={item.label}
                href={item.href}
                className="rounded-md px-3 py-2 text-sm font-medium text-white/80 transition hover:bg-white/5 hover:text-white"
              >
                {item.label}
              </Link>
            )
          )}
        </nav>

        <div className="flex items-center gap-3">
          <a
            href="https://github.com/Lampx83/LakeFlow"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden items-center gap-1.5 rounded-md px-3 py-2 text-sm text-white/70 hover:text-white sm:flex"
            aria-label="GitHub"
          >
            <GitHubIcon className="h-5 w-5" />
            <span>GitHub</span>
          </a>
          <Link
            href="/#hero"
            className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-400"
          >
            Get Started
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
