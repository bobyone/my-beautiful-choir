// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { describe, expect, it } from "vitest";

import { createI18n } from "./i18n";

describe("createI18n", () => {
  it("defaults to English", async () => {
    const i18n = await createI18n();
    expect(i18n.t("about.title", { name: "my-beautiful-choir" })).toBe("About my-beautiful-choir");
  });

  it("formats ICU messages with named parameters", async () => {
    const i18n = await createI18n("hu");
    expect(i18n.t("about.title", { name: "my-beautiful-choir" })).toBe(
      "A(z) my-beautiful-choir névjegye",
    );
  });

  it("uses the glossary labels", async () => {
    const i18n = await createI18n("fr");
    expect(i18n.t("glossary.personalMode")).toBe("Mode perso");
    expect(i18n.t("glossary.webMode")).toBe("Mode web");
  });

  it("falls back to English for an unknown language", async () => {
    const i18n = await createI18n("ja");
    expect(i18n.t("about.version")).toBe("Version");
  });
});
