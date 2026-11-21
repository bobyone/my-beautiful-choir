// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

export const DEFAULT_LANGUAGE = "en";

/**
 * Chooses the catalogue to display for a host locale (BCP 47), trying in order:
 * the full tag, then language and script, then the language alone (as given,
 * then canonicalized); at each
 * step, an available catalogue, then a declared fallback (e.g. `cnr` →
 * `sr-Latn`). English otherwise.
 */
export function resolveLanguage(
  locale: string | undefined,
  available: readonly string[],
  fallbacks: Readonly<Record<string, string>>,
): string {
  if (locale === undefined || locale === "") {
    return DEFAULT_LANGUAGE;
  }
  let parsed: Intl.Locale;
  try {
    parsed = new Intl.Locale(locale);
  } catch {
    return DEFAULT_LANGUAGE;
  }
  const byLowerCase = new Map(available.map((code) => [code.toLowerCase(), code]));
  // The original language subtag is also tried: ICU canonicalizes some tags,
  // e.g. Montenegrin `cnr` becomes `sr-ME`, which would lose its fallback.
  const originalLanguage = locale.split(/[-_]/)[0]?.toLowerCase();
  const candidates = [
    parsed.baseName,
    parsed.script === undefined ? undefined : `${parsed.language}-${parsed.script}`,
    originalLanguage,
    parsed.language,
  ];
  for (const candidate of candidates) {
    if (candidate === undefined) {
      continue;
    }
    const direct = byLowerCase.get(candidate.toLowerCase());
    if (direct !== undefined) {
      return direct;
    }
    const fallback = fallbacks[candidate];
    if (fallback !== undefined && byLowerCase.has(fallback.toLowerCase())) {
      return fallback;
    }
  }
  return DEFAULT_LANGUAGE;
}
