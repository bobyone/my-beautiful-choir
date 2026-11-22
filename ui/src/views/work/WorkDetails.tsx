// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { useTranslation } from "react-i18next";

import type { WorkResult } from "./workInfo";

function displayLanguage(names: Intl.DisplayNames, code: string): string {
  try {
    return names.of(code) ?? code;
  } catch {
    return code;
  }
}

export function WorkDetails({ data }: { data: WorkResult }) {
  const { t, i18n } = useTranslation();
  const { work, choir } = data;
  const languages = new Intl.DisplayNames(i18n.language, { type: "language" });
  const list = new Intl.ListFormat(i18n.language);
  const rows = [
    [t("glossary.choir"), choir],
    [t("glossary.composer"), work.composer],
    [t("glossary.arranger"), work.arranger],
    [t("glossary.voicing"), work.voicing],
    [
      t("glossary.sungLanguage"),
      list.format(work.sungLanguages.map((language) => displayLanguage(languages, language))),
    ],
    [t("glossary.notes"), work.notes],
  ];
  return (
    <dl className="row">
      {rows
        .filter(([, value]) => Boolean(value))
        .map(([label, value]) => (
          <div key={label} className="d-sm-flex gap-2">
            <dt className="col-sm-4">{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
    </dl>
  );
}
