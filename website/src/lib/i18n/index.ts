import { en } from "./locales/en";
import { vi } from "./locales/vi";
import { zh } from "./locales/zh";
import { hi } from "./locales/hi";
import { es } from "./locales/es";
import { fr } from "./locales/fr";

export const BUILTIN_LOCALES = ["en", "vi", "zh", "hi", "es", "fr"] as const;
export type BuiltinLocale = (typeof BUILTIN_LOCALES)[number];
export type Locale = BuiltinLocale | string;

const STORAGE_KEY = "lakeflow-website-locale";

export function getStoredLocale(): Locale {
  if (typeof window === "undefined") return "en";
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (!v) return "en";
    if (BUILTIN_LOCALES.includes(v as BuiltinLocale)) return v as BuiltinLocale;
  } catch (_) {}
  return "en";
}

export function setStoredLocale(locale: Locale) {
  try {
    localStorage.setItem(STORAGE_KEY, String(locale));
  } catch (_) {}
}

export const translations: Record<BuiltinLocale, Record<string, string>> = {
  en,
  vi,
  zh,
  hi,
  es,
  fr,
};

export function t(locale: Locale, key: string): string {
  const loc = String(locale);
  const builtin = BUILTIN_LOCALES.includes(loc as BuiltinLocale)
    ? translations[loc as BuiltinLocale]?.[key]
    : undefined;
  if (builtin) return builtin;
  return translations.en?.[key] ?? key;
}

export function isValidLocaleCode(code: string): code is BuiltinLocale {
  return BUILTIN_LOCALES.includes(code as BuiltinLocale);
}

const LOCALE_LABELS: Record<BuiltinLocale, string> = {
  en: "English",
  vi: "Tiếng Việt",
  zh: "中文",
  hi: "हिन्दी",
  es: "Español",
  fr: "Français",
};

const LOCALE_FLAGS: Record<BuiltinLocale, string> = {
  en: "🇺🇸",
  vi: "🇻🇳",
  zh: "🇨🇳",
  hi: "🇮🇳",
  es: "🇪🇸",
  fr: "🇫🇷",
};

export function getLocaleLabel(locale: string): string {
  if (BUILTIN_LOCALES.includes(locale as BuiltinLocale))
    return LOCALE_LABELS[locale as BuiltinLocale] ?? locale;
  return locale;
}

export function getLocaleFlag(locale: string): string {
  if (BUILTIN_LOCALES.includes(locale as BuiltinLocale))
    return LOCALE_FLAGS[locale as BuiltinLocale] ?? "";
  return "";
}
