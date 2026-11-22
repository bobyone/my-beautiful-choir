// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { CalledToolResult, ToolResult } from "../host/useHost";

export type CallTool = (name: string, args: Record<string, unknown>) => Promise<CalledToolResult>;

export function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function resultData(result: ToolResult): Record<string, unknown> | undefined {
  return result.isError === true || !record(result.structuredContent)
    ? undefined
    : result.structuredContent;
}

export function nonnegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}

export function textOrNull(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

export function parseList<T>(
  items: unknown,
  parse: (item: unknown) => T | undefined,
): T[] | undefined {
  if (!Array.isArray(items)) return undefined;
  const parsed = items.map(parse);
  return parsed.every((item) => item !== undefined) ? parsed : undefined;
}
