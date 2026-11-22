// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { ToolResult } from "../../host/useHost";
import { nonnegativeInteger, parseList, record, resultData, textOrNull } from "../viewData";
import { parseWork, type WorkInfo } from "../work/workInfo";

interface RepertoireWork extends WorkInfo {
  scoreCount: number;
}

export interface RepertoireInfo {
  choir: string | null;
  choirs: string[];
  works: RepertoireWork[];
  search: string;
}

function parseChoir(value: unknown): string | undefined {
  return record(value) && typeof value["name"] === "string" ? value["name"] : undefined;
}

function parseRepertoireWork(value: unknown): RepertoireWork | undefined {
  if (!record(value) || !nonnegativeInteger(value["score_count"])) return undefined;
  const work = parseWork(value);
  return work && { ...work, scoreCount: value["score_count"] };
}

export function parseRepertoire(result: ToolResult): RepertoireInfo | undefined {
  const data = resultData(result);
  if (!data || !textOrNull(data["choir"]) || typeof data["search"] !== "string") return undefined;
  const choirs = parseList(data["choirs"], parseChoir);
  const works = parseList(data["works"], parseRepertoireWork);
  return choirs && works
    ? { choir: data["choir"], choirs, works, search: data["search"] }
    : undefined;
}
