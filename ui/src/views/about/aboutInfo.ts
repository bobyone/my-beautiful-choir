// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { ToolResult } from "../../host/useHost";

export type Mode = "personal" | "web";

/** Information returned by the `show_about` tool. */
export interface AboutInfo {
  name: string;
  version: string;
  mode: Mode;
}

/** Reads the structured content of a `show_about` result; undefined when invalid or an error. */
export function parseAboutInfo(result: ToolResult): AboutInfo | undefined {
  if (result.isError === true) {
    return undefined;
  }
  const content: unknown = result.structuredContent;
  if (typeof content !== "object" || content === null) {
    return undefined;
  }
  const { name, version, mode } = content as Record<string, unknown>;
  if (
    typeof name !== "string" ||
    typeof version !== "string" ||
    (mode !== "personal" && mode !== "web")
  ) {
    return undefined;
  }
  return { name, version, mode };
}
