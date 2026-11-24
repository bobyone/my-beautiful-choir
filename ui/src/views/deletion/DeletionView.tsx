// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import type { TFunction } from "i18next";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import Spinner from "react-bootstrap/Spinner";
import { useTranslation } from "react-i18next";

import type { DeletionSummary, DeletionTarget } from "./deletionInfo";

export type DeletionState =
  | { kind: "loading" }
  | { kind: "connection-error" }
  | { kind: "error" }
  | {
      kind: "pending" | "deleting" | "deleted" | "nothing-deleted" | "failed";
      deletion: DeletionSummary;
      refreshed?: boolean;
    };

export interface DeletionActions {
  onDelete: () => void;
  onCancel: () => void;
}

/** "Deletion" view: what will be deleted, with "Delete" and "Cancel" buttons. */
export function DeletionView({
  state,
  onDelete,
  onCancel,
}: { state: DeletionState } & DeletionActions) {
  const { t } = useTranslation();

  switch (state.kind) {
    case "loading":
      return <Waiting text={t("deletion.loading")} />;
    case "connection-error":
      return (
        <Alert variant="danger" className="m-3">
          {t("connection.error")}
        </Alert>
      );
    case "error":
      return (
        <Alert variant="danger" className="m-3">
          {t("deletion.error")}
        </Alert>
      );
    default:
      return (
        <Card as="main" className="m-3">
          <Card.Body>
            <Card.Title as="h1" className="h5">
              {t("glossary.deletion")}
            </Card.Title>
            <DeletionSummaryView deletion={state.deletion} />
            {state.refreshed && state.kind === "pending" && (
              <Alert variant="info">{t("deletion.nothingDeleted")}</Alert>
            )}
            <Outcome kind={state.kind} onDelete={onDelete} onCancel={onCancel} />
          </Card.Body>
        </Card>
      );
  }
}

function Waiting({ text }: { text: string }) {
  return (
    <div className="d-flex align-items-center gap-2 p-3" role="status">
      <Spinner animation="border" size="sm" aria-hidden="true" />
      <span>{text}</span>
    </div>
  );
}

function Outcome({
  kind,
  onDelete,
  onCancel,
}: { kind: "pending" | "deleting" | "deleted" | "nothing-deleted" | "failed" } & DeletionActions) {
  const { t } = useTranslation();
  switch (kind) {
    case "pending":
      return (
        <>
          <Alert variant="warning">{t("deletion.warning")}</Alert>
          <div className="d-flex flex-wrap gap-2">
            <Button variant="danger" onClick={onDelete}>
              {t("deletion.delete")}
            </Button>
            <Button variant="secondary" onClick={onCancel}>
              {t("deletion.cancel")}
            </Button>
          </div>
        </>
      );
    case "deleting":
      return <Waiting text={t("deletion.deleting")} />;
    case "deleted":
      return (
        <Alert variant="success" className="mb-0">
          {t("deletion.done")}
        </Alert>
      );
    case "nothing-deleted":
      return (
        <Alert variant="info" className="mb-0">
          {t("deletion.nothingDeleted")}
        </Alert>
      );
    case "failed":
      return (
        <Alert variant="danger" className="mb-0">
          {t("deletion.failed")}
        </Alert>
      );
  }
}

export function DeletionSummaryView({ deletion }: { deletion: DeletionSummary }) {
  const { t, i18n } = useTranslation();
  const number = new Intl.NumberFormat(i18n.language);
  const parentTarget: DeletionTarget | undefined =
    deletion.target === "work" ? "choir" : deletion.target === "score" ? "work" : undefined;
  const addedAt = deletion.addedAt;

  return (
    <dl className="row">
      <dt className="col-sm-4">{targetLabel(deletion.target, t)}</dt>
      <dd className="col-sm-8">
        {deletion.movementNumber === undefined
          ? deletion.name
          : t("glossary.movement", { number: deletion.movementNumber })}
        {addedAt !== undefined && (
          <time className="d-block" dateTime={addedAt}>
            {new Intl.DateTimeFormat(i18n.language, {
              dateStyle: "short",
              timeStyle: "medium",
            }).format(new Date(addedAt))}
          </time>
        )}
      </dd>
      {parentTarget !== undefined && deletion.parentName !== null && (
        <>
          <dt className="col-sm-4">{targetLabel(parentTarget, t)}</dt>
          <dd className="col-sm-8">{deletion.parentName}</dd>
        </>
      )}
      {deletion.workCount > 0 && (
        <>
          <dt className="col-sm-4">{t("deletion.works")}</dt>
          <dd className="col-sm-8">{number.format(deletion.workCount)}</dd>
        </>
      )}
      {deletion.scoreCount > 0 && (
        <>
          <dt className="col-sm-4">{t("deletion.scores")}</dt>
          <dd className="col-sm-8">{number.format(deletion.scoreCount)}</dd>
        </>
      )}
    </dl>
  );
}

/** Glossary label of a kind of element. */
function targetLabel(target: DeletionTarget, t: TFunction): string {
  switch (target) {
    case "choir":
      return t("glossary.choir");
    case "work":
      return t("glossary.work");
    case "score":
      return t("glossary.score");
  }
}
