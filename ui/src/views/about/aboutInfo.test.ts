// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { describe, expect, it } from "vitest";

import { parseAboutInfo } from "./aboutInfo";

const info = { name: "my-beautiful-choir", version: "1.2.3", mode: "web" };

describe("parseAboutInfo", () => {
  it("reads the structured content", () => {
    expect(parseAboutInfo({ content: [], structuredContent: info })).toEqual(info);
  });

  it.each([
    ["an error result", { content: [], isError: true, structuredContent: info }],
    ["no structured content", { content: [] }],
    ["an unknown mode", { content: [], structuredContent: { ...info, mode: "cloud" } }],
    ["a missing version", { content: [], structuredContent: { name: "x", mode: "web" } }],
    ["a non-text name", { content: [], structuredContent: { ...info, name: 3 } }],
  ])("rejects %s", (_, result) => {
    expect(parseAboutInfo(result)).toBeUndefined();
  });
});
