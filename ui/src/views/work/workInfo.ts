// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { DownloadableFile, ToolResult } from "../../host/useHost";
import { nonnegativeInteger, parseList, record, resultData, textOrNull } from "../viewData";

export interface WorkInfo {
  id: string;
  title: string;
  composer: string | null;
  arranger: string | null;
  voicing: string | null;
  notes: string | null;
  sungLanguages: string[];
}

export interface ScoreInfo {
  id: string;
  label: string;
  format: "pdf" | "musicxml" | "mxl" | "mscz";
  size: number;
}

export interface WorkResult {
  choir: string;
  work: WorkInfo;
  scores: ScoreInfo[];
  supportsTranscription?: boolean;
}

export function parseWork(value: unknown): WorkInfo | undefined {
  if (!record(value)) return undefined;
  const { id, title, composer, arranger, voicing, notes, sung_languages: languages } = value;
  if (
    typeof id !== "string" ||
    typeof title !== "string" ||
    !textOrNull(composer) ||
    !textOrNull(arranger) ||
    !textOrNull(voicing) ||
    !textOrNull(notes) ||
    !Array.isArray(languages) ||
    !languages.every((language): language is string => typeof language === "string")
  )
    return undefined;
  return { id, title, composer, arranger, voicing, notes, sungLanguages: languages };
}

export function parseScore(value: unknown): ScoreInfo | undefined {
  if (!record(value)) return undefined;
  const { id, label, format, size } = value;
  if (
    typeof id !== "string" ||
    typeof label !== "string" ||
    !nonnegativeInteger(size) ||
    (format !== "pdf" && format !== "musicxml" && format !== "mxl" && format !== "mscz")
  )
    return undefined;
  return { id, label, format, size };
}

/** The score file a tool returned as an embedded resource, if any. */
export function scoreFile(result: ToolResult): DownloadableFile | undefined {
  if (result.isError === true) return undefined;
  return result.content.find(
    (item): item is Extract<DownloadableFile, { type: "resource" }> =>
      item.type === "resource" && "blob" in item.resource && typeof item.resource.blob === "string",
  );
}

export function parseWorkResult(result: ToolResult): WorkResult | undefined {
  const data = resultData(result);
  if (data === undefined || typeof data["choir"] !== "string") return undefined;
  const work = parseWork(data["work"]);
  const scores = parseList(data["scores"], parseScore);
  if (!work || !scores) return undefined;
  const workResult: WorkResult = { choir: data["choir"], work, scores };
  if (data["supports_transcription"] === true) workResult.supportsTranscription = true;
  return workResult;
}
