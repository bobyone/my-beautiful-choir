// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { Resource } from "i18next";

import fallbacks from "../../i18n/fallbacks.json";

/** Every catalogue of `locales/`, keyed by language code (the file name). */
const modules = import.meta.glob<Record<string, unknown>>("../../locales/*.json", {
  eager: true,
  import: "default",
});

function languageOf(path: string): string {
  const fileName = path.split("/").pop() ?? path;
  return fileName.replace(/\.json$/, "");
}

export const RESOURCES: Resource = Object.fromEntries(
  Object.entries(modules).map(([path, catalogue]) => [
    languageOf(path),
    { translation: catalogue },
  ]),
);

/** Languages with a catalogue: adding a language only requires adding its file. */
export const AVAILABLE_LANGUAGES: readonly string[] = Object.keys(RESOURCES).sort();

/** Fallbacks for languages without a catalogue (e.g. `cnr` → `sr-Latn`). */
export const FALLBACKS: Readonly<Record<string, string>> = fallbacks;
