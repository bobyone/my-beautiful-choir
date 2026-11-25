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
const movement = {
  target: "score",
  name: "Movement 2",
  parent_name: "Ave Maria",
  work_count: 0,
  score_count: 0,
  movement_number: 2,
  added_at: "2026-11-24T09:30:00+00:00",
};
const concert = {
  target: "event",
  name: "Christmas concert",
  parent_name: "Chœur de Lyon",
  work_count: 0,
  score_count: 0,
  event_kind: "concert",
  starts_at: "2026-12-20T19:30:00+00:00",
  programme_entry_count: 3,
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

  it("parses movement details from a score deletion", () => {
    expect(
      parseDeletionInfo({
        content: [],
        structuredContent: { status: "pending", deletion: movement, token: "test-token" },
      }),
    ).toMatchObject({
      deletion: { movementNumber: 2, addedAt: movement.added_at },
    });
  });

  it("parses an event deletion", () => {
    expect(
      parseDeletionInfo({
        content: [],
        structuredContent: { status: "deleted", deletion: concert },
      }),
    ).toEqual({
      status: "deleted",
      deletion: {
        target: "event",
        name: "Christmas concert",
        parentName: "Chœur de Lyon",
        workCount: 0,
        scoreCount: 0,
        eventKind: "concert",
        startsAt: concert.starts_at,
        programmeEntryCount: 3,
      },
    });
  });

  it("parses the events counted by a work deletion", () => {
    expect(
      parseDeletionInfo({
        content: [],
        structuredContent: {
          status: "deleted",
          deletion: { ...deletion, target: "work", event_count: 2 },
        },
      }),
    ).toMatchObject({ deletion: { eventCount: 2 } });
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
    { status: "deleted", deletion: { ...movement, movement_number: 0 } },
    { status: "deleted", deletion: { ...movement, target: "work" } },
    { status: "deleted", deletion: { ...movement, movement_number: undefined } },
    { status: "deleted", deletion: { ...movement, added_at: "invalid" } },
    { status: "deleted", deletion: { ...deletion, event_count: -1 } },
    { status: "deleted", deletion: { ...concert, programme_entry_count: 1.5 } },
    { status: "deleted", deletion: { ...concert, event_kind: "party" } },
    { status: "deleted", deletion: { ...concert, event_kind: undefined } },
    { status: "deleted", deletion: { ...concert, starts_at: "invalid" } },
  ])("rejects a malformed deletion result", (structuredContent) => {
    expect(parseDeletionInfo({ content: [], structuredContent })).toBeUndefined();
  });
});
