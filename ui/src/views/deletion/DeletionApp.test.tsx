// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createI18n } from "../../i18n/i18n";
import { FakeHost } from "../../test/fakeHost";
import { DeletionApp } from "./DeletionApp";

const mocked = vi.hoisted(() => ({
  host: undefined as { useApp: (options: never) => unknown } | undefined,
}));

vi.mock("@modelcontextprotocol/ext-apps/react", () => ({
  useApp: (options: never) => mocked.host?.useApp(options),
  useHostStyles: vi.fn(),
}));

const deletion = {
  target: "work",
  name: "Ave Maria",
  parent_name: "Chœur de Lyon",
  work_count: 0,
  score_count: 2,
};

function result(status: "pending" | "deleted" | "refused") {
  return { content: [], structuredContent: { status, deletion, token: "test-token" } };
}

describe("DeletionApp", () => {
  let host: FakeHost;

  beforeEach(() => {
    host = new FakeHost();
    mocked.host = host;
  });

  async function renderApp(): Promise<void> {
    const i18n = await createI18n("en");
    render(<DeletionApp i18n={i18n} />);
  }

  it("waits for the summary and sends the token only when the user clicks Delete", async () => {
    host.answerToolCall = () => result("deleted");
    await renderApp();
    expect(screen.getByRole("status").textContent).toBe("Loading the deletion details…");
    act(() => {
      host.sendToolResult(result("pending"));
    });

    expect(screen.getByRole("heading", { name: "Deletion" })).toBeDefined();
    expect(screen.getByText("Ave Maria")).toBeDefined();
    expect(screen.getByText("Chœur de Lyon")).toBeDefined();
    expect(screen.getByText("Scores")).toBeDefined();
    expect(screen.getByText("2")).toBeDefined();
    expect(host.toolCalls).toEqual([]);

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(screen.getByRole("status").textContent).toBe("Deleting…");
    expect(await screen.findByText("Deletion complete.")).toBeDefined();
    expect(host.toolCalls).toEqual([
      { name: "confirm_deletion", arguments: { token: "test-token" } },
    ]);
    expect(screen.queryByRole("button", { name: "Delete" })).toBeNull();
  });

  it("cancels without calling the host", async () => {
    await renderApp();
    act(() => {
      host.sendToolResult(result("pending"));
    });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByText("Nothing was deleted.")).toBeDefined();
    expect(host.toolCalls).toEqual([]);
  });

  it.each([
    ["deleted", "Deletion complete."],
    ["refused", "Nothing was deleted."],
  ] as const)("shows a %s outcome returned by elicitation", async (status, text) => {
    await renderApp();
    act(() => {
      host.sendToolResult(result(status));
    });
    expect(screen.getByText(text)).toBeDefined();
    expect(screen.queryByRole("button", { name: "Delete" })).toBeNull();
    expect(host.toolCalls).toEqual([]);
  });

  it.each(["server", "transport"])("explains a %s confirmation failure", async (failure) => {
    if (failure === "server") {
      host.answerToolCall = () => ({ content: [], isError: true });
    } else {
      host.toolCallError = new Error("Disconnected");
    }
    await renderApp();
    act(() => {
      host.sendToolResult(result("pending"));
    });
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(
      await screen.findByText("The deletion failed. Ask the assistant to try again."),
    ).toBeDefined();
    expect(host.toolCalls).toHaveLength(1);
  });

  it("explains an invalid result", async () => {
    await renderApp();
    act(() => {
      host.sendToolResult({ content: [] });
    });
    expect(screen.getByRole("alert").textContent).toContain("could not be displayed");
    expect(host.toolCalls).toEqual([]);
  });

  it("explains a connection error", async () => {
    host.connected = false;
    host.error = new Error("Disconnected");
    await renderApp();
    expect(screen.getByRole("alert").textContent).toContain("could not connect");
  });
});
