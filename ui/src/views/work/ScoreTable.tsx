// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

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
  onDelete: (score: ScoreInfo) => void;
}

export function ScoreTable({ scores, busy, onOpen, onDelete }: ScoreTableProps) {
  const { t, i18n } = useTranslation();
  const bytes = new Intl.NumberFormat(i18n.language, {
    style: "unit",
    unit: "byte",
    unitDisplay: "short",
  });
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
              {score.label}
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
