// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import Alert from "react-bootstrap/Alert";
import Card from "react-bootstrap/Card";
import Spinner from "react-bootstrap/Spinner";
import { useTranslation } from "react-i18next";

import type { AboutInfo } from "./aboutInfo";

export type AboutState =
  | { kind: "loading" }
  | { kind: "connection-error" }
  | { kind: "error" }
  | { kind: "ready"; info: AboutInfo };

/** "About" view: name, version and mode of my-beautiful-choir. */
export function AboutView({ state }: { state: AboutState }) {
  const { t } = useTranslation();

  switch (state.kind) {
    case "loading":
      return (
        <div className="d-flex align-items-center gap-2 p-3" role="status">
          <Spinner animation="border" size="sm" aria-hidden="true" />
          <span>{t("about.loading")}</span>
        </div>
      );
    case "connection-error":
      return (
        <Alert variant="danger" className="m-3">
          {t("connection.error")}
        </Alert>
      );
    case "error":
      return (
        <Alert variant="danger" className="m-3">
          {t("about.error")}
        </Alert>
      );
    case "ready": {
      const { name, version, mode } = state.info;
      return (
        <Card as="main" className="m-3">
          <Card.Body>
            <Card.Title as="h1" className="h5">
              {t("about.title", { name })}
            </Card.Title>
            <dl className="row mb-0">
              <dt className="col-sm-4">{t("about.version")}</dt>
              <dd className="col-sm-8">{version}</dd>
              <dt className="col-sm-4">{t("glossary.mode")}</dt>
              <dd className="col-sm-8 mb-0">
                {mode === "web" ? t("glossary.webMode") : t("glossary.personalMode")}
              </dd>
            </dl>
          </Card.Body>
        </Card>
      );
    }
  }
}
