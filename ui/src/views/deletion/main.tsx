// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import "bootstrap/dist/css/bootstrap.min.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { createI18n } from "../../i18n/i18n";
import { DeletionApp } from "./DeletionApp";

const root = document.getElementById("root");
if (root !== null) {
  const i18n = await createI18n();
  createRoot(root).render(
    <StrictMode>
      <DeletionApp i18n={i18n} />
    </StrictMode>,
  );
}
