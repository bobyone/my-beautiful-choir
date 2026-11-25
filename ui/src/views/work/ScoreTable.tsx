// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-FileContributor: bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Table from "react-bootstrap/Table";
import { useTranslation } from "react-i18next";

import type { ScoreInfo } from "./workInfo";

const FORMATS: Record<ScoreInfo["format"], string> = {
  pdf: "PDF",
  musicxml: "MusicXML",
  mxl: "MXL",
  mscz: "MuseScore",
};

interface ScoreTableProps {
  scores: ScoreInfo[];
  busy: boolean;
  onOpen: (score: ScoreInfo) => void;
  /** Without it, the Download action is not shown. */
  onDownload?: ((score: ScoreInfo) => void) | undefined;
  onDelete: (score: ScoreInfo) => void;
  onDuplicate?: (score: ScoreInfo) => void;
  onFinalise?: ((score: ScoreInfo) => void) | undefined;
  onDownloadPdf?: ((score: ScoreInfo) => void) | undefined;
  availableOrigins?: ReadonlySet<string> | undefined;
  timeZone?: string | undefined;
  onTranscribe?: ((score: ScoreInfo) => void) | undefined;
}

export function ScoreTable({
  scores,
  busy,
  onOpen,
  onDownload,
  onDelete,
  onTranscribe,
  onDuplicate,
  onFinalise,
  onDownloadPdf,
  availableOrigins,
  timeZone,
}: ScoreTableProps) {
  const { t, i18n } = useTranslation();
  const bytes = new Intl.NumberFormat(i18n.language, {
    style: "unit",
    unit: "byte",
    unitDisplay: "short",
  });
  const dates = new Intl.DateTimeFormat(i18n.language, { dateStyle: "medium", timeZone });
  const numbers = new Intl.NumberFormat(i18n.language, { useGrouping: false });
  return scores.length === 0 ? (
    <p>{t("work.noScores")}</p>
  ) : (
    <Table responsive striped>
      <caption className="visually-hidden">{t("deletion.scores")}</caption>
      <thead>
        <tr>
          <th scope="col">{t("glossary.scoreLabel")}</th>
          <th scope="col">{t("glossary.scoreFormat")}</th>
          <th scope="col">{t("glossary.scoreSize")}</th>
          <th scope="col" className="visually-hidden">
            {t("view.actions")}
          </th>
        </tr>
      </thead>
      <tbody>
        {scores.map((score) => (
          <tr key={score.id}>
            <th id={`score-${score.id}`} scope="row">
              {score.movementNumber === undefined
                ? score.label
                : t("glossary.movement", { number: score.movementNumber })}
              {score.state && (
                <div className="d-flex flex-wrap align-items-center gap-2">
                  <Badge
                    bg={score.state === "draft" ? "warning" : "secondary"}
                    text={score.state === "draft" ? "dark" : "light"}
                  >
                    {score.state === "draft" ? t("work.draftScore") : t("work.finalScore")}
                  </Badge>
                  {score.versionNumber && `v${numbers.format(score.versionNumber)}`}
                  {score.draftDate && dates.format(new Date(score.draftDate))}
                </div>
              )}
              {score.originatingScore && (
                <div className="small fw-normal">
                  {availableOrigins?.has(score.originatingScore.id) ? (
                    <a href={`#score-${score.originatingScore.id}`}>
                      {t("work.originatingScore", score.originatingScore)}
                    </a>
                  ) : (
                    t("work.originatingScore", score.originatingScore)
                  )}
                </div>
              )}
            </th>
            <td>{FORMATS[score.format]}</td>
            <td>{bytes.format(score.size)}</td>
            <td>
              <div className="d-flex flex-wrap gap-2">
                <Button
                  variant="outline-primary"
                  disabled={busy}
                  aria-describedby={`score-${score.id}`}
                  onClick={() => {
                    onOpen(score);
                  }}
                >
                  {t("work.openScore")}
                </Button>
                {onDownload !== undefined && (
                  <Button
                    variant="outline-primary"
                    disabled={busy}
                    aria-describedby={`score-${score.id}`}
                    onClick={() => {
                      onDownload(score);
                    }}
                  >
                    {t("work.downloadScore")}
                  </Button>
                )}
                {onTranscribe !== undefined && score.format === "pdf" && (
                  <Button
                    variant="outline-primary"
                    disabled={busy}
                    aria-describedby={`score-${score.id}`}
                    onClick={() => {
                      onTranscribe(score);
                    }}
                  >
                    {t("work.transcribeScore")}
                  </Button>
                )}
                {onDuplicate &&
                  score.state === "final" &&
                  (score.format === "musicxml" || score.format === "mxl") && (
                    <Button
                      variant="outline-primary"
                      disabled={busy}
                      aria-describedby={`score-${score.id}`}
                      onClick={() => {
                        onDuplicate(score);
                      }}
                    >
                      {t("work.duplicateDraft")}
                    </Button>
                  )}
                {onFinalise && score.state === "draft" && (
                  <Button
                    variant="outline-primary"
                    disabled={busy}
                    aria-describedby={`score-${score.id}`}
                    onClick={() => {
                      onFinalise(score);
                    }}
                  >
                    {t("work.finaliseScore")}
                  </Button>
                )}
                {onDownloadPdf && (score.format === "musicxml" || score.format === "mxl") && (
                  <Button
                    variant="outline-primary"
                    disabled={busy}
                    aria-describedby={`score-${score.id}`}
                    onClick={() => {
                      onDownloadPdf(score);
                    }}
                  >
                    {t("work.downloadPdf")}
                  </Button>
                )}
                <Button
                  variant="outline-danger"
                  disabled={busy}
                  aria-describedby={`score-${score.id}`}
                  onClick={() => {
                    onDelete(score);
                  }}
                >
                  {t("deletion.delete")}
                </Button>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
