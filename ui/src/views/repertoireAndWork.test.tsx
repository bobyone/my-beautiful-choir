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
    { ...work, id: "second", title: "Alleluia", score_count: 0 },
    { ...work, score_count: 1 },
  ],
  search: "",
  page: 1,
  page_size: 10,
  page_count: 1,
  work_count: 2,
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

/** The element the next Tab press reaches after ``element``. */
function nextTabStop(element: Element): Element | undefined {
  const stops = [
    ...document.querySelectorAll("a[href], button, input, select, textarea, [tabindex]"),
  ].filter((item) => item.getAttribute("tabindex") !== "-1" && !item.hasAttribute("disabled"));
  return stops.find(
    (item) => element.compareDocumentPosition(item) & Node.DOCUMENT_POSITION_FOLLOWING,
  );
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
    { page: 0 },
    { page: 2 },
    { page_size: 0 },
    { page_count: 1.5 },
    { work_count: -1 },
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

  it("shows and searches a repertoire in the server order and switches choirs", async () => {
    host.answerToolCall = () => result({ ...repertoire, choir: "Paris", works: [] });
    const { container } = await show(RepertoireApp, result(repertoire));
    const rows = screen.getAllByRole("row");
    expect(rows.map((row) => row.textContent)).toEqual([
      "TitleComposerVoicingScores",
      "AlleluiaLili BoulangerSATB0",
      "ÉtoileLili BoulangerSATB1",
    ]);
    expect(screen.getByText("2 works")).toBeDefined();
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(await accessibilityViolations(container)).toEqual([]);
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "boulanger" } });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Paris" } });
    await screen.findByText("No works found.");
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => {
      expect(host.toolCalls).toEqual([
        {
          name: "show_repertoire",
          arguments: { choir: "Paris", search: "boulanger", page_size: 10 },
        },
        {
          name: "show_repertoire",
          arguments: { choir: "Paris", search: "boulanger", page_size: 10 },
        },
      ]);
    });
  });

  it("recognizes a stored PDF and displays the transcription", async () => {
    const recognized = { id: "xml", label: "Transcription", format: "musicxml", size: 180 };
    host.answerToolCall = ({ name }) =>
      name === "transcribe_score"
        ? result({ state: "pending", job_id: "job" })
        : result({ state: "done", score: recognized });
    await show(WorkApp, result({ ...workResult, supports_transcription: true }));
    fireEvent.click(screen.getByRole("button", { name: "Transcribe the score" }));
    expect(screen.getByRole("status", { name: "Transcription" })).toBeDefined();
    expect(
      await screen.findByText("Transcription available.", {}, { timeout: 3000 }),
    ).toBeDefined();
    expect(screen.getByRole("rowheader", { name: "Transcription" })).toBeDefined();
    expect(screen.getAllByRole("button", { name: "Transcribe the score" })).toHaveLength(1);
    expect(host.toolCalls).toEqual([
      { name: "transcribe_score", arguments: { score_id: score.id } },
      { name: "get_transcription_status", arguments: { job_id: "job" } },
    ]);
  });

  it("shows all movements in order and does not duplicate a reused result", async () => {
    const movements = [1, 2, 10].map((number) => ({
      id: `movement-${number.toString()}`,
      label: "Stored label",
      movement_number: number,
      format: "musicxml",
      size: 180,
    }));
    host.answerToolCall = () => result({ state: "done", scores: movements });
    await show(WorkApp, result({ ...workResult, supports_transcription: true }));
    const button = screen.getByRole("button", { name: "Transcribe the score" });
    fireEvent.click(button);
    await screen.findByRole("rowheader", { name: "Movement 10" });
    fireEvent.click(button);
    await waitFor(() => {
      expect(host.toolCalls).toHaveLength(2);
    });
    expect(screen.getAllByRole("rowheader").map((row) => row.textContent)).toEqual([
      "Soprano",
      "Movement 1",
      "Movement 2",
      "Movement 10",
    ]);
  });

  it("offers the official installation link when Audiveris is missing", async () => {
    host.answerToolCall = () =>
      result({
        state: "failed",
        error_code: "engine_missing",
        install_url: "https://audiveris.github.io/audiveris/_pages/tutorials/install/binaries/",
      });
    await show(WorkApp, result({ ...workResult, supports_transcription: true }));
    fireEvent.click(screen.getByRole("button", { name: "Transcribe the score" }));
    const link = await screen.findByRole("link", { name: "Audiveris" });
    expect(link.getAttribute("href")).toContain("audiveris.github.io");
  });

  it("pages through the repertoire", async () => {
    const paged = { ...repertoire, search: "li", page_size: 2, page_count: 3, work_count: 5 };
    host.answerToolCall = ({ arguments: args }) => result({ ...paged, page: args?.["page"] });
    const { container } = await show(RepertoireApp, result(paged));
    const pages = screen.getByRole("navigation", { name: "Repertoire pages" });
    expect(within(pages).getByText("Page 1 of 3").getAttribute("aria-current")).toBe("page");
    expect(within(pages).queryByRole("button", { name: "Previous" })).toBeNull();
    expect(await accessibilityViolations(container)).toEqual([]);
    fireEvent.click(within(pages).getByRole("button", { name: "Next" }));
    expect(await screen.findByText("Page 2 of 3")).toBeDefined();
    const results = screen.getByRole("heading", { name: "5 works" });
    expect(document.activeElement).toBe(results);
    expect(nextTabStop(results)).toBe(screen.getByRole("button", { name: "Alleluia" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("Page 3 of 3")).toBeDefined();
    expect(screen.queryByRole("button", { name: "Next" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Previous" }));
    expect(await screen.findByText("Page 2 of 3")).toBeDefined();
    expect(host.toolCalls.map(({ arguments: args }) => args)).toEqual(
      [2, 3, 2].map((page) => ({ choir, search: "li", page, page_size: 2 })),
    );
  });

  it("opens a work from the repertoire and returns to the same page", async () => {
    const second = { ...repertoire, page: 2, page_count: 2, work_count: 12 };
    host.answerToolCall = ({ name }) => result(name === "show_work" ? workResult : second);
    await show(RepertoireApp, result(second));
    fireEvent.click(screen.getByRole("button", { name: work.title }));
    expect(await screen.findByRole("heading", { name: work.title })).toBeDefined();
    expect(screen.getByText(/Latin/)).toBeDefined();
    expect(screen.getByText(/fr-FR-FR/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Back to repertoire" }));
    expect(await screen.findByRole("heading", { name: "Repertoire" })).toBeDefined();
    await waitFor(() => {
      expect(host.toolCalls.map(({ name }) => name)).toEqual(["show_work", "show_repertoire"]);
    });
    expect(host.toolCalls[1]?.arguments).toEqual({
      choir,
      search: "",
      page: 2,
      page_size: 10,
    });
    await waitFor(() => {
      expect(document.activeElement).toBe(screen.getByRole("button", { name: work.title }));
    });
  });

  it("focuses the results when the opened work is no longer listed", async () => {
    const without = { ...repertoire, works: [repertoire.works[0]], work_count: 1 };
    host.answerToolCall = ({ name }) => result(name === "show_work" ? workResult : without);
    await show(RepertoireApp, result(repertoire));
    fireEvent.click(screen.getByRole("button", { name: work.title }));
    fireEvent.click(await screen.findByRole("button", { name: "Back to repertoire" }));
    const results = await screen.findByRole("heading", { name: "1 work" });
    await waitFor(() => {
      expect(document.activeElement).toBe(results);
    });
  });

  it("prompts for a choir when the repertoire is empty", async () => {
    await show(RepertoireApp, result({ ...repertoire, choir: null, choirs: [], works: [] }));
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

  it("hides Download when the host cannot save files", async () => {
    await show(WorkApp, result(workResult));
    expect(screen.getByRole("button", { name: "Open" })).toBeDefined();
    expect(screen.queryByRole("button", { name: "Download" })).toBeNull();
  });

  it("downloads a score through the host and reports each outcome", async () => {
    const file = {
      type: "resource",
      resource: { uri: "file:///Soprano.pdf", mimeType: "application/pdf", blob: "UERG" },
    } as const;
    host.capabilities = { downloadFile: {} };
    host.answerToolCall = () => ({ content: [{ type: "text", text: "Here is the file" }, file] });
    const { container } = await show(WorkApp, result(workResult));
    const download = screen.getByRole("button", { name: "Download" });
    expect(download.getAttribute("aria-describedby")).toBe(`score-${score.id}`);
    expect(await accessibilityViolations(container)).toEqual([]);

    fireEvent.click(download);
    expect(screen.getByRole("status")).toBeDefined();
    expect(screen.getByRole("button", { name: "Download" }).hasAttribute("disabled")).toBe(true);
    expect(await screen.findByText("Score downloaded.")).toBeDefined();
    expect(host.toolCalls).toEqual([{ name: "download_score", arguments: { score_id: score.id } }]);
    expect(host.downloads).toEqual([[file]]);

    host.downloadAnswer = { isError: true };
    fireEvent.click(screen.getByRole("button", { name: "Download" }));
    expect(await screen.findByText("Download cancelled.")).toBeDefined();

    host.downloadAnswer = new Error("lost");
    fireEvent.click(screen.getByRole("button", { name: "Download" }));
    expect(await screen.findByText(/Could not download the score/)).toBeDefined();

    host.answerToolCall = () => error;
    fireEvent.click(screen.getByRole("button", { name: "Download" }));
    await waitFor(() => {
      expect(host.toolCalls).toHaveLength(4);
    });
    expect(await screen.findByText(/It may have been deleted/)).toBeDefined();
    expect(host.downloads).toHaveLength(3);

    host.answerToolCall = () => ({ content: [{ type: "text", text: "No file" }] });
    fireEvent.click(screen.getByRole("button", { name: "Download" }));
    await waitFor(() => {
      expect(host.toolCalls).toHaveLength(5);
    });
    expect(await screen.findByText(/Could not download the score/)).toBeDefined();
    expect(host.downloads).toHaveLength(3);
  });

  it("offers Download in a work opened from the repertoire", async () => {
    host.capabilities = { downloadFile: {} };
    host.answerToolCall = () => result(workResult);
    await show(RepertoireApp, result(repertoire));
    fireEvent.click(screen.getByRole("button", { name: work.title }));
    expect(await screen.findByRole("button", { name: "Download" })).toBeDefined();
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
