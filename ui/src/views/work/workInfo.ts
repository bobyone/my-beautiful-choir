// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-FileContributor: bobyone
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
  movementNumber?: number;
  state?: "draft" | "final";
  versionNumber?: number;
  draftDate?: string;
  originatingScore?: { id: string; label: string; versionNumber: number };
}

export interface WorkResult {
  choir: string;
  work: WorkInfo;
  scores: ScoreInfo[];
  supportsTranscription?: boolean;
  supportsFinalisation?: boolean;
  supportsPdfExport?: boolean;
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
  const { id, label, format, size, movement_number: movementNumber } = value;
  if (
    typeof id !== "string" ||
    typeof label !== "string" ||
    !nonnegativeInteger(size) ||
    (format !== "pdf" && format !== "musicxml" && format !== "mxl" && format !== "mscz")
  )
    return undefined;
  const score: ScoreInfo = { id, label, format, size };
  if (movementNumber !== undefined) {
    if (!nonnegativeInteger(movementNumber) || movementNumber === 0) return undefined;
    score.movementNumber = movementNumber;
  }
  const { state, version_number: version, draft_date: date, originating_score: origin } = value;
  if (state === "draft" || state === "final") score.state = state;
  if (nonnegativeInteger(version) && version > 0) score.versionNumber = version;
  if (typeof date === "string" && Number.isFinite(Date.parse(date))) score.draftDate = date;
  if (record(origin)) {
    const { id: originId, label: originLabel, version_number: originVersion } = origin;
    if (
      typeof originId === "string" &&
      typeof originLabel === "string" &&
      nonnegativeInteger(originVersion) &&
      originVersion > 0
    ) {
      score.originatingScore = { id: originId, label: originLabel, versionNumber: originVersion };
    }
  }
  return score;
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
  if (data["supports_finalisation"] === true) workResult.supportsFinalisation = true;
  if (data["supports_pdf_export"] === true) workResult.supportsPdfExport = true;
  return workResult;
}
