// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { describe, expect, it, vi } from "vitest";

import { createI18n } from "../../i18n/i18n";
import { accessibilityViolations } from "../../test/accessibility";
import { DeletionView, type DeletionState } from "./DeletionView";
import type { DeletionSummary } from "./deletionInfo";

const choir: DeletionSummary = {
  target: "choir",
  name: "Chœur de Lyon",
  parentName: null,
  workCount: 1234,
  scoreCount: 5678,
};

async function renderView(state: DeletionState, language = "en") {
  const i18n = await createI18n(language);
  return render(
    <I18nextProvider i18n={i18n}>
      <DeletionView state={state} onDelete={vi.fn()} onCancel={vi.fn()} />
    </I18nextProvider>,
  );
}

describe("DeletionView", () => {
  it("formats the work and score totals in the view language", async () => {
    await renderView({ kind: "pending", deletion: choir }, "fr");
    expect(screen.getByRole("heading", { name: "Suppression" })).toBeDefined();
    expect(screen.getByText("Chorale")).toBeDefined();
    expect(screen.getByRole("button", { name: "Supprimer" })).toBeDefined();
    expect(screen.getByText("Œuvres")).toBeDefined();
    expect(screen.getByText("Partitions")).toBeDefined();
    const totals = new Intl.NumberFormat("fr");
    expect(screen.getByText(totals.format(1234), { normalizer: (value) => value })).toBeDefined();
    expect(screen.getByText(totals.format(5678), { normalizer: (value) => value })).toBeDefined();
  });

  it("shows a score and its work, without empty counts", async () => {
    await renderView({
      kind: "pending",
      deletion: {
        target: "score",
        name: "Soprano",
        parentName: "Ave Maria",
        workCount: 0,
        scoreCount: 0,
      },
    });
    for (const text of ["Score", "Soprano", "Work", "Ave Maria"]) {
      expect(screen.getByText(text)).toBeDefined();
    }
    expect(screen.queryByText("Works")).toBeNull();
    expect(screen.queryByText("Scores")).toBeNull();
  });

  it.each<DeletionState>([
    { kind: "loading" },
    { kind: "connection-error" },
    { kind: "error" },
    { kind: "pending", deletion: choir },
    { kind: "deleting", deletion: choir },
    { kind: "deleted", deletion: choir },
    { kind: "nothing-deleted", deletion: choir },
    { kind: "failed", deletion: choir },
  ])("has no accessibility violation ($kind)", async (state) => {
    const { container } = await renderView(state);
    expect(await accessibilityViolations(container)).toEqual([]);
  });
});
