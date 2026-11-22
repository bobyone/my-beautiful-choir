// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createI18n } from "../i18n/i18n";
import { accessibilityViolations } from "../test/accessibility";
import { FakeHost } from "../test/fakeHost";
import type { ToolResult } from "../host/useHost";
import { RepertoireApp } from "./repertoire/RepertoireApp";
import { parseRepertoire } from "./repertoire/repertoireInfo";
import { WorkApp } from "./work/WorkApp";
import { parseWorkResult } from "./work/workInfo";

const mocked = vi.hoisted(() => ({
  host: undefined as { useApp: (options: never) => unknown } | undefined,
}));
vi.mock("@modelcontextprotocol/ext-apps/react", () => ({
  useApp: (options: never) => mocked.host?.useApp(options),
  useHostStyles: vi.fn(),
}));

const work = {
  id: "work",
  title: "Étoile",
  composer: "Lili Boulanger",
  arranger: "Jane",
  voicing: "SATB",
  notes: "Opening work",
  sung_languages: ["fr", "la", "fr-FR-FR"],
};
const score = { id: "score", label: "Soprano", format: "pdf", size: 200 };
const choir = "Lyon";
const repertoire = {
  choir,
  choirs: [{ name: choir }, { name: "Paris" }],
  works: [
    { ...work, score_count: 1 },
    { ...work, id: "second", title: "Alleluia", score_count: 0 },
  ],
  search: "",
};
const workResult = { choir, work, scores: [score] };
const deleted = {
  status: "deleted",
  deletion: { target: "work", name: work.title, parent_name: choir, work_count: 0, score_count: 1 },
};
const error = { content: [], isError: true };
function result(structuredContent: Record<string, unknown>): ToolResult {
  return { content: [], structuredContent };
}

describe("view result validation", () => {
  it.each([
    { choir: 1 },
    { choirs: [{ name: false }] },
    { works: [{ ...work, score_count: -1 }] },
    { works: [{ ...work, score_count: 1.5 }] },
    { works: [null] },
    { works: {} },
    { search: false },
  ])("rejects an invalid repertoire payload", (fields) => {
    expect(parseRepertoire(result({ ...repertoire, ...fields }))).toBeUndefined();
  });

  it.each([
    { choir: false },
    { work: [] },
    { work: { ...work, title: 1 } },
    { work: { ...work, sung_languages: ["fr", 1] } },
    { scores: null },
    { scores: [{ ...score, size: "200" }] },
    { scores: [{ ...score, size: -1 }] },
    { scores: [{ ...score, format: "exe" }] },
    { scores: [{}] },
  ])("rejects an invalid work payload", (fields) => {
    expect(parseWorkResult(result({ ...workResult, ...fields }))).toBeUndefined();
  });
});

describe("repertoire and work views", () => {
  let host: FakeHost;

  async function show(App: typeof WorkApp | typeof RepertoireApp, data?: ToolResult) {
    const i18n = await createI18n("en");
    const rendered = render(<App i18n={i18n} />);
    if (data)
      act(() => {
        host.sendToolResult(data);
      });
    return rendered;
  }

  beforeEach(() => {
    host = new FakeHost();
    mocked.host = host;
  });

  it("shows and searches a sorted repertoire and switches choirs", async () => {
    host.answerToolCall = () => result({ ...repertoire, choir: "Paris", works: [] });
    const { container } = await show(RepertoireApp, result(repertoire));
    const rows = screen.getAllByRole("row");
    expect(rows.map((row) => row.textContent)).toEqual([
      "TitleComposerVoicingScores",
      "AlleluiaLili BoulangerSATB0",
      "ÉtoileLili BoulangerSATB1",
    ]);
    expect(await accessibilityViolations(container)).toEqual([]);
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "boulanger" } });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Paris" } });
    await screen.findByText("No works found.");
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => {
      expect(host.toolCalls).toEqual([
        { name: "show_repertoire", arguments: { choir: "Paris", search: "boulanger" } },
        { name: "show_repertoire", arguments: { choir: "Paris", search: "boulanger" } },
      ]);
    });
  });

  it("opens a work from the repertoire and refreshes after returning", async () => {
    host.answerToolCall = ({ name }) => result(name === "show_work" ? workResult : repertoire);
    await show(RepertoireApp, result(repertoire));
    fireEvent.click(screen.getByRole("button", { name: work.title }));
    expect(await screen.findByRole("heading", { name: work.title })).toBeDefined();
    expect(screen.getByText(/Latin/)).toBeDefined();
    expect(screen.getByText(/fr-FR-FR/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Back to repertoire" }));
    expect(await screen.findByRole("heading", { name: "Repertoire" })).toBeDefined();
    await waitFor(() => {
      expect(host.toolCalls.map(({ name }) => name)).toEqual(["show_work", "show_repertoire"]);
    });
  });

  it("prompts for a choir when the repertoire is empty", async () => {
    await show(RepertoireApp, result({ choir: null, choirs: [], works: [], search: "" }));
    expect(screen.getByText("No choirs yet. Ask the assistant to create one.")).toBeDefined();
  });

  it("shows failed search and work requests", async () => {
    host.answerToolCall = () => error;
    await show(RepertoireApp, result(repertoire));
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    expect(await screen.findByRole("alert")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: work.title }));
    expect(await screen.findByRole("alert")).toBeDefined();
  });

  it.each([RepertoireApp, WorkApp])(
    "reports loading, an invalid result and a connection failure",
    async (App) => {
      const { unmount } = await show(App);
      expect(screen.getByRole("status")).toBeDefined();
      act(() => {
        host.sendToolResult(error);
      });
      expect(screen.getByRole("alert").textContent).toContain("could not be displayed");
      unmount();
      host = new FakeHost();
      mocked.host = host;
      host.connected = false;
      host.error = new Error("Disconnected");
      await show(App);
      expect(screen.getByRole("alert").textContent).toContain("could not connect");
    },
  );

  it("shows work details and opens a score through the host", async () => {
    const { container } = await show(WorkApp, result(workResult));
    expect(screen.getByText("Soprano")).toBeDefined();
    expect(screen.getByText("Opening work")).toBeDefined();
    expect(await accessibilityViolations(container)).toEqual([]);
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    expect(await screen.findByText("Score opened.")).toBeDefined();
    expect(host.toolCalls).toEqual([{ name: "open_score", arguments: { score_id: score.id } }]);
    host.answerToolCall = () => error;
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    expect(await screen.findByText(/Could not open the score/)).toBeDefined();
  });

  it("sends only the chosen file and updates the score table", async () => {
    const uploaded = { id: "new", label: "Alto", format: "mxl", size: 3 };
    host.answerToolCall = () => result({ score: uploaded });
    const { container } = await show(WorkApp, result({ ...workResult, scores: [] }));
    expect(screen.getByText("No scores yet.")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Add a score" }));
    const picker = container.querySelector("input[type=file]");
    if (!picker) throw new Error("Expected a file picker.");
    fireEvent.change(picker, { target: { files: [new File(["PDF"], "Alto.mxl")] } });
    expect(await screen.findByText("Score added.")).toBeDefined();
    expect(screen.getByText("Alto")).toBeDefined();
    expect(host.toolCalls).toEqual([
      {
        name: "upload_score",
        arguments: { work_id: work.id, file_name: "Alto.mxl", content: "UERG" },
      },
    ]);
    fireEvent.change(picker, { target: { files: [new File([], "Empty.pdf")] } });
    expect(await screen.findByText(/Upload failed/)).toBeDefined();
    expect(host.toolCalls).toHaveLength(1);
  });

  it("asks again when a work changes while its confirmation is open", async () => {
    host.answerToolCall = ({ name, arguments: args }) => {
      if (name === "preview_work_deletion") {
        return result({ ...deleted, status: "pending", token: "original" });
      }
      if (args?.["token"] === "original") {
        return result({
          status: "pending",
          token: "refreshed",
          deletion: { ...deleted.deletion, name: "Gloria", score_count: 2 },
        });
      }
      return result(deleted);
    };
    await show(WorkApp, result(workResult));
    fireEvent.click(screen.getByRole("button", { name: "Delete the work" }));
    let dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));
    expect(await screen.findByText("Gloria")).toBeDefined();
    dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Nothing was deleted.")).toBeDefined();
    expect(within(dialog).getByText("2")).toBeDefined();
    expect(host.toolCalls).toHaveLength(2);
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));
    expect(await screen.findByText("Deletion complete.")).toBeDefined();
    expect(host.toolCalls.at(-1)?.arguments).toEqual({ token: "refreshed" });
  });

  it("requires confirmation to delete a score or the work", async () => {
    host.answerToolCall = ({ name, arguments: args }) => {
      const removingWork = name === "preview_work_deletion" || args?.["token"] === "work-token";
      const deletion = removingWork
        ? deleted.deletion
        : {
            ...deleted.deletion,
            target: "score",
            name: score.label,
            parent_name: work.title,
            score_count: 0,
          };
      return name === "confirm_deletion"
        ? result({ ...deleted, deletion })
        : result({
            status: "pending",
            deletion,
            token: removingWork ? "work-token" : "score-token",
          });
    };
    await show(WorkApp, result(workResult));
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    let dialog = await screen.findByRole("dialog");
    expect(await accessibilityViolations(dialog)).toEqual([]);
    fireEvent.click(within(dialog).getByRole("button", { name: "Cancel" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
    expect(host.toolCalls).toEqual([
      { name: "preview_score_deletion", arguments: { target_id: score.id } },
    ]);
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));
    expect(await screen.findByText("No scores yet.")).toBeDefined();
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
    fireEvent.click(screen.getByRole("button", { name: "Delete the work" }));
    dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("The scores of this work will also be deleted.")).toBeDefined();
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: "Delete the work" })).toBeNull();
    });
    expect(host.toolCalls).toEqual([
      { name: "preview_score_deletion", arguments: { target_id: score.id } },
      { name: "preview_score_deletion", arguments: { target_id: score.id } },
      { name: "confirm_deletion", arguments: { token: "score-token" } },
      { name: "preview_work_deletion", arguments: { target_id: work.id } },
      { name: "confirm_deletion", arguments: { token: "work-token" } },
    ]);
  });
});
