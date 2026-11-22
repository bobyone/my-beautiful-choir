// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FakeHost } from "../test/fakeHost";
import { useHost } from "./useHost";

const mocked = vi.hoisted(() => ({
  host: undefined as { useApp: (options: never) => unknown } | undefined,
  useHostStyles: vi.fn(),
}));

vi.mock("@modelcontextprotocol/ext-apps/react", () => ({
  useApp: (options: never) => mocked.host?.useApp(options),
  useHostStyles: mocked.useHostStyles,
}));

describe("useHost", () => {
  let host: FakeHost;

  beforeEach(() => {
    host = new FakeHost();
    mocked.host = host;
    mocked.useHostStyles.mockClear();
  });

  it("starts connected, without result, with the initial host context", () => {
    host.initialContext = { locale: "fr-FR", theme: "dark" };
    const { result } = renderHook(() => useHost("view", "1.0.0"));
    expect(result.current).toMatchObject({
      connected: true,
      connectionFailed: false,
      hostContext: { locale: "fr-FR", theme: "dark" },
      toolResult: undefined,
    });
    expect(mocked.useHostStyles).toHaveBeenCalledWith(host.app, {
      locale: "fr-FR",
      theme: "dark",
    });
  });

  it("receives the tool result", () => {
    const { result } = renderHook(() => useHost("view", "1.0.0"));
    act(() => {
      host.sendToolResult({ content: [], structuredContent: { a: 1 } });
    });
    expect(result.current.toolResult).toEqual({ content: [], structuredContent: { a: 1 } });
  });

  it("merges host context changes", () => {
    host.initialContext = { locale: "fr-FR", theme: "dark" };
    const { result } = renderHook(() => useHost("view", "1.0.0"));
    act(() => {
      host.changeHostContext({ theme: "light" });
    });
    act(() => {
      host.changeHostContext({ locale: "de-DE" });
    });
    expect(result.current.hostContext).toEqual({ locale: "de-DE", theme: "light" });
  });

  it("keeps the initial context fields that a change does not carry", () => {
    host.initialContext = { locale: "fr-FR", theme: "light" };
    const { result } = renderHook(() => useHost("view", "1.0.0"));
    act(() => {
      host.changeHostContext({ theme: "dark" });
    });
    expect(result.current.hostContext).toEqual({ locale: "fr-FR", theme: "dark" });
  });

  it("reports a failed connection and rejects tool calls", async () => {
    host.connected = false;
    host.error = new Error("timeout");
    const { result } = renderHook(() => useHost("view", "1.0.0"));
    expect(result.current.connected).toBe(false);
    expect(result.current.connectionFailed).toBe(true);
    expect(mocked.useHostStyles).toHaveBeenCalledWith(null, undefined);
    await expect(result.current.callTool("confirm_deletion", {})).rejects.toThrow("not connected");
    expect(host.toolCalls).toEqual([]);
  });
});
