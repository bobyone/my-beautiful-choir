// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-FileContributor: bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { ToolResult } from "../../host/useHost";
import { record, resultData } from "../viewData";
import { parseScore, type ScoreInfo } from "./workInfo";

export interface FinalisationInfo {
  score: ScoreInfo;
  token: string;
}

export function parseFinalisation(result: ToolResult): FinalisationInfo | undefined {
  const score = parseScore(resultData(result)?.["finalisation"]);
  const metadata = result._meta;
  const token = record(metadata) && metadata["finalisation_token"];
  if (score?.state !== "draft" || typeof token !== "string" || token.length === 0) return undefined;
  return { score, token };
}
