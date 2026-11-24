// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-FileContributor: bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { type CallTool, parseList, resultData } from "../viewData";
import { parseScore, type ScoreInfo } from "./workInfo";

export type TranscriptionOutcome =
  | { state: "pending" }
  | { state: "done"; scores: ScoreInfo[] }
  | {
      state: "failed";
      errorKey?: "work.transcriptionInstall" | "work.transcriptionUnavailable";
      installUrl?: string | undefined;
    };

export async function requestTranscription(
  callTool: CallTool,
  scoreId: string,
): Promise<Exclude<TranscriptionOutcome, { state: "pending" }>> {
  let status = resultData(await callTool("transcribe_score", { score_id: scoreId }));
  while (status?.["state"] === "pending" && typeof status["job_id"] === "string") {
    const jobId = status["job_id"];
    await new Promise<void>((resolve) => setTimeout(resolve, 1000));
    status = resultData(await callTool("get_transcription_status", { job_id: jobId }));
  }
  if (status?.["state"] === "done") {
    const data = status["scores"];
    const scores = parseList(data === undefined ? [status["score"]] : data, parseScore);
    if (scores && scores.length > 0) return { state: "done", scores };
  }
  const installUrl = httpsLink(status?.["install_url"]);
  if (status?.["error_code"] === "engine_missing") {
    return { state: "failed", errorKey: "work.transcriptionInstall", installUrl };
  }
  if (status?.["error_code"] === "engine_unavailable") {
    return { state: "failed", errorKey: "work.transcriptionUnavailable", installUrl };
  }
  return { state: "failed" };
}

function httpsLink(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.href : undefined;
  } catch {
    return undefined;
  }
}
