// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { describe, expect, it } from "vitest";

import { AVAILABLE_LANGUAGES, FALLBACKS } from "./catalogues";
import { resolveLanguage } from "./resolveLanguage";

const resolve = (locale: string | undefined) =>
  resolveLanguage(locale, AVAILABLE_LANGUAGES, FALLBACKS);

describe("resolveLanguage", () => {
  it.each([
    ["fr", "fr"],
    ["fr-BE", "fr"],
    ["pt-BR", "pt"],
    ["de-AT", "de"],
    ["sr-Latn-RS", "sr-Latn"],
    ["sr-Cyrl", "sr-Cyrl"],
    ["sr", "sr-Cyrl"],
    ["sr-RS", "sr-Cyrl"],
    ["cnr", "sr-Latn"],
    ["cnr-ME", "sr-Latn"],
    ["no", "nb"],
    ["nn-NO", "nn"],
    ["EL-gr", "el"],
  ])("resolves %s to %s", (locale, expected) => {
    expect(resolve(locale)).toBe(expected);
  });

  it.each([[undefined], [""], ["ja-JP"], ["not a locale!"]])(
    "falls back to English for %s",
    (locale) => {
      expect(resolve(locale)).toBe("en");
    },
  );

  it("ignores a fallback whose catalogue is missing", () => {
    expect(resolveLanguage("cnr", ["en"], { cnr: "sr-Latn" })).toBe("en");
  });
});

describe("catalogues", () => {
  it("covers the 42 catalogues of the target languages", () => {
    expect(AVAILABLE_LANGUAGES).toHaveLength(42);
    expect(AVAILABLE_LANGUAGES).toContain("en");
    expect(AVAILABLE_LANGUAGES).not.toContain("cnr");
  });
});
