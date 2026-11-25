// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-FileContributor: bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import { useTranslation } from "react-i18next";

import type { FinalisationInfo } from "./finalisationInfo";

export function ScoreFinalisationDialog({
  preview,
  onCancel,
  onConfirm,
}: {
  preview: FinalisationInfo | undefined;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Modal show={preview !== undefined} onHide={onCancel} aria-labelledby="confirm-finalisation">
      <Modal.Header>
        <Modal.Title id="confirm-finalisation">{t("work.finaliseScore")}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {preview && t("work.finalisationQuestion", { label: preview.score.label })}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" autoFocus onClick={onCancel}>
          {t("deletion.cancel")}
        </Button>
        <Button onClick={onConfirm}>{t("work.finaliseScore")}</Button>
      </Modal.Footer>
    </Modal>
  );
}
