// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { ToolResult } from "../../host/useHost";

export type DeletionTarget = "choir" | "work" | "score";

/** What a deletion removes: an element and everything it contains. */
export interface DeletionSummary {
  target: DeletionTarget;
  name: string;
  /** Choir of a work, or work of a score. */
  parentName: string | null;
  workCount: number;
  scoreCount: number;
  movementNumber?: number;
  addedAt?: string;
}

/** Result of `delete_choir`, `delete_work`, `delete_score` and `confirm_deletion`. */
export type DeletionInfo =
  | { status: "deleted" | "refused"; deletion: DeletionSummary }
  | { status: "pending"; deletion: DeletionSummary; token: string };

const TARGETS: readonly string[] = ["choir", "work", "score"];

function isCount(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function parseSummary(value: unknown): DeletionSummary | undefined {
  if (typeof value !== "object" || value === null) {
    return undefined;
  }
  const { target, name, parent_name, work_count, score_count, movement_number, added_at } =
    value as Record<string, unknown>;
  if (
    typeof target !== "string" ||
    !TARGETS.includes(target) ||
    typeof name !== "string" ||
    (parent_name !== null && typeof parent_name !== "string") ||
    !isCount(work_count) ||
    !isCount(score_count) ||
    (movement_number !== undefined &&
      (target !== "score" || !isCount(movement_number) || movement_number === 0)) ||
    (added_at !== undefined &&
      (movement_number === undefined ||
        typeof added_at !== "string" ||
        !Number.isFinite(Date.parse(added_at))))
  ) {
    return undefined;
  }
  return {
    target: target as DeletionTarget,
    name,
    parentName: parent_name,
    workCount: work_count,
    scoreCount: score_count,
    ...(movement_number === undefined ? {} : { movementNumber: movement_number }),
    ...(added_at === undefined ? {} : { addedAt: added_at }),
  };
}

/** Reads the structured content of a deletion result; undefined when invalid or an error. */
export function parseDeletionInfo(result: ToolResult): DeletionInfo | undefined {
  if (result.isError === true) {
    return undefined;
  }
  const content: unknown = result.structuredContent;
  if (typeof content !== "object" || content === null) {
    return undefined;
  }
  const { status, deletion, token } = content as Record<string, unknown>;
  const summary = parseSummary(deletion);
  if (summary === undefined) {
    return undefined;
  }
  if (status === "pending") {
    return typeof token === "string" && token !== ""
      ? { status, deletion: summary, token }
      : undefined;
  }
  if (status === "deleted" || status === "refused") {
    return { status, deletion: summary };
  }
  return undefined;
}
