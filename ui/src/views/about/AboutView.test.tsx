// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { describe, expect, it } from "vitest";

import { createI18n } from "../../i18n/i18n";
import { accessibilityViolations } from "../../test/accessibility";
import { AboutView, type AboutState } from "./AboutView";

async function renderView(state: AboutState, language = "en") {
  const i18n = await createI18n(language);
  return render(
    <I18nextProvider i18n={i18n}>
      <AboutView state={state} />
    </I18nextProvider>,
  );
}

const ready: AboutState = {
  kind: "ready",
  info: { name: "my-beautiful-choir", version: "1.2.3", mode: "web" },
};

describe("AboutView", () => {
  it("announces the loading", async () => {
    await renderView({ kind: "loading" });
    expect(screen.getByRole("status").textContent).toBe("Loading the information…");
  });

  it("shows the name, version and mode", async () => {
    await renderView(ready);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("About my-beautiful-choir");
    expect(screen.getByText("1.2.3")).toBeDefined();
    expect(screen.getByText("Web mode")).toBeDefined();
  });

  it("shows the personal mode with its glossary label", async () => {
    await renderView({ kind: "ready", info: { ...ready.info, mode: "personal" } }, "fr");
    expect(screen.getByText("Mode perso")).toBeDefined();
  });

  it("explains a result error and how to recover", async () => {
    await renderView({ kind: "error" });
    expect(screen.getByRole("alert").textContent).toContain("Ask the assistant to show it again");
  });

  it("explains a connection error and how to recover", async () => {
    await renderView({ kind: "connection-error" });
    expect(screen.getByRole("alert").textContent).toContain("Close it, then try again");
  });

  it.each<AboutState>([
    { kind: "loading" },
    { kind: "error" },
    { kind: "connection-error" },
    ready,
  ])("has no accessibility violation ($kind)", async (state) => {
    const { container } = await renderView(state);
    expect(await accessibilityViolations(container)).toEqual([]);
  });
});
