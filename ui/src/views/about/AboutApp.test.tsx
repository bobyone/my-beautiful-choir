// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createI18n } from "../../i18n/i18n";
import { FakeHost } from "../../test/fakeHost";
import { AboutApp } from "./AboutApp";

const mocked = vi.hoisted(() => ({
  host: undefined as { useApp: (options: never) => unknown } | undefined,
}));

vi.mock("@modelcontextprotocol/ext-apps/react", () => ({
  useApp: (options: never) => mocked.host?.useApp(options),
  useHostStyles: vi.fn(),
}));

const aboutResult = {
  content: [{ type: "text" as const, text: "my-beautiful-choir 1.2.3, personal mode." }],
  structuredContent: { name: "my-beautiful-choir", version: "1.2.3", mode: "personal" },
};

async function renderApp(): Promise<void> {
  const i18n = await createI18n();
  render(<AboutApp i18n={i18n} />);
}

describe("AboutApp", () => {
  let host: FakeHost;

  beforeEach(() => {
    host = new FakeHost();
    mocked.host = host;
  });

  it("waits for the tool result, then displays it", async () => {
    await renderApp();
    expect(screen.getByRole("status")).toBeDefined();
    act(() => {
      host.sendToolResult(aboutResult);
    });
    expect(screen.getByText("1.2.3")).toBeDefined();
    expect(screen.getByText("Personal mode")).toBeDefined();
  });

  it("follows the host language and theme", async () => {
    host.initialContext = { locale: "de-DE", theme: "dark" };
    await renderApp();
    act(() => {
      host.sendToolResult(aboutResult);
    });
    await waitFor(() => {
      expect(screen.getByText("Persönlicher Modus")).toBeDefined();
    });
    expect(document.documentElement.lang).toBe("de");
    expect(document.documentElement.dataset["bsTheme"]).toBe("dark");

    act(() => {
      host.changeHostContext({ locale: "cnr-ME", theme: "light" });
    });
    await waitFor(() => {
      expect(screen.getByText("Lični režim rada")).toBeDefined();
    });
    expect(document.documentElement.lang).toBe("sr-Latn");
    expect(document.documentElement.dataset["bsTheme"]).toBe("light");
  });

  it("shows an error for an invalid result", async () => {
    await renderApp();
    act(() => {
      host.sendToolResult({ content: [], isError: true });
    });
    expect(screen.getByRole("alert").textContent).toContain("could not be displayed");
  });

  it("shows a connection error", async () => {
    host.connected = false;
    host.error = new Error("timeout");
    await renderApp();
    expect(screen.getByRole("alert").textContent).toContain("could not connect");
  });
});
