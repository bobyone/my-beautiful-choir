// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import Alert from "react-bootstrap/Alert";
import Spinner from "react-bootstrap/Spinner";
import { useTranslation } from "react-i18next";

export function ViewStatus({ kind }: { kind: "loading" | "connection-error" | "error" }) {
  const { t } = useTranslation();
  if (kind === "loading") {
    return (
      <div className="p-3 d-flex gap-2 align-items-center" role="status">
        <Spinner size="sm" aria-hidden="true" />
        {t("view.loading")}
      </div>
    );
  }
  return (
    <Alert variant="danger" className="m-3">
      {kind === "connection-error" ? t("connection.error") : t("view.error")}
    </Alert>
  );
}
