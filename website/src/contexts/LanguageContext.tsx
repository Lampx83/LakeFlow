"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import {
  getStoredLocale,
  setStoredLocale,
  t as tFn,
  type Locale,
} from "@/lib/i18n";

type LanguageContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const stored = getStoredLocale();
    setLocaleState(stored);
    if (typeof document !== "undefined") document.documentElement.lang = stored;
  }, [mounted]);

  const setLocale = useCallback((value: Locale) => {
    setLocaleState(value);
    setStoredLocale(value);
    if (typeof document !== "undefined") document.documentElement.lang = value;
  }, []);

  const t = useCallback((key: string) => tFn(locale, key), [locale]);

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    return {
      locale: "en" as Locale,
      setLocale: (_: Locale) => {},
      t: (key: string) => tFn("en", key),
    };
  }
  return ctx;
}
