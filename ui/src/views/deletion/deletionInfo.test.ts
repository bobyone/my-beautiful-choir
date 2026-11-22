// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { describe, expect, it } from "vitest";

import { parseDeletionInfo } from "./deletionInfo";

const deletion = {
  target: "choir",
  name: "Chœur de Lyon",
  parent_name: null,
  work_count: 1,
  score_count: 2,
};

describe("parseDeletionInfo", () => {
  it("converts a valid payload to the view representation", () => {
    expect(
      parseDeletionInfo({
        content: [],
        structuredContent: { status: "pending", deletion, token: "test-token" },
      }),
    ).toEqual({
      status: "pending",
      deletion: {
        target: "choir",
        name: "Chœur de Lyon",
        parentName: null,
        workCount: 1,
        scoreCount: 2,
      },
      token: "test-token",
    });
  });

  it.each([
    { status: "pending", deletion, token: "" },
    { status: "pending", deletion, token: 5 },
    { status: "unknown", deletion },
    { status: "deleted", deletion: null },
    { status: "deleted", deletion: { ...deletion, target: "unknown" } },
    { status: "deleted", deletion: { ...deletion, target: 9 } },
    { status: "deleted", deletion: { ...deletion, name: undefined } },
    { status: "deleted", deletion: { ...deletion, parent_name: 9 } },
    { status: "deleted", deletion: { ...deletion, work_count: -1 } },
    { status: "deleted", deletion: { ...deletion, score_count: 1.5 } },
    { status: "deleted", deletion: { ...deletion, score_count: "2" } },
  ])("rejects a malformed deletion result", (structuredContent) => {
    expect(parseDeletionInfo({ content: [], structuredContent })).toBeUndefined();
  });
});
